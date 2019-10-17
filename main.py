import click
import requests
from tabulate import tabulate


def get_table_data(table_data, headers, indent_level=0):
    tabulate_table = tabulate(table_data, headers, tablefmt='fancy_grid')
    if indent_level > 0:
        tabulate_table = (' ' * indent_level) + tabulate_table.replace('\n', '\n' + (' ' * indent_level))
    return tabulate_table

class DND5EAPI:
    ENDPOINT_URL = 'http://dnd5eapi.co/api'
    
    @classmethod
    def get_abilities(cls, name=None):
        ability_data = requests.get(f'{cls.ENDPOINT_URL}/ability-scores/').json()
        if name is not None:
            ability_data = next(filter(lambda x: x['name'].lower() == name.lower(),
                                       ability_data['results']))
            ability_details = requests.get(ability_data['url']).json()
            return ability_details
        return ability_data['results']
    
    @classmethod
    def get_skills(cls, name=None):
        skill_data = requests.get(f'{cls.ENDPOINT_URL}/skills/').json()
        if name is not None:
            skill_data = next(filter(lambda x: x['name'].lower().startswith(name.lower()),
                                     skill_data['results']))
            skill_details = requests.get(skill_data['url']).json()
            return skill_details
        return skill_data['results']
    
    @classmethod
    def get_proficiencies(cls, char_class=None):
        url = f'{cls.ENDPOINT_URL}/proficiencies/'
        if char_class is not None:
            url += char_class
        proficiency_data = requests.get(url).json()
        return proficiency_data['results']
    
    @classmethod
    def get_languages(cls, name=None):
        url = f'{cls.ENDPOINT_URL}/languages/'
        language_data = requests.get(url).json()
        if name is not None:
            language_data = next(filter(lambda x: x['name'].lower().startswith(name.lower()),
                                        language_data['results']))
            language_details = requests.get(language_data['url']).json()
            return language_details
        return language_data['results']
    
    @classmethod
    def get_classes(cls, name=None):
        class_data = requests.get(f'{cls.ENDPOINT_URL}/classes/').json()
        if name is not None:
            class_data = next(filter(lambda x: x['name'].lower().startswith(name.lower()),
                                     class_data['results']))
            class_details = requests.get(class_data['url']).json()
            if 'starting_equipment' in class_details:
                class_details['starting_equipment'] = requests.get(class_details['starting_equipment']['url']).json()
            if 'spellcasting' in class_details:
                class_details['spellcasting'] = requests.get(class_details['spellcasting']['url']).json()
            return class_details
        return class_data['results']
    
    @classmethod
    def get_subclasses(cls, char_class=None, subclass=None):
        url = f'{cls.ENDPOINT_URL}/subclasses/'
        if char_class is not None:
            url += char_class
        subclass_data = requests.get(url).json()
        if subclass is not None:
            subclass_data = next(filter(lambda x: x['name'].lower().startswith(subclass.lower()),
                                 subclass_data['results']))
            subclass_details = requests.get(subclass_data['url']).json()
            if 'features' in subclass_details and subclass_details['features']:
                for feature_index, feature in enumerate(subclass_details['features']):
                    subclass_details['features'][feature_index] = requests.get(feature['url']).json()
            return subclass_details
        return subclass_data['results']
    
    @classmethod
    def get_class_levels(cls, class_name, class_level):
        level_data = requests.get(f'{cls.ENDPOINT_URL}/classes/{class_name}/level/{class_level}').json()
        if 'features' in level_data and level_data['features']:
            for feature_index, feature in enumerate(level_data['features']):
                level_data['features'][feature_index] = requests.get(feature['url']).json()

        return level_data



@click.group()
def cli():
    pass


@click.command()
@click.argument('ability', required=False, default=None)
def abilities(ability):
    ability_data = DND5EAPI.get_abilities(ability)
    if ability is None:
        click.echo('\n'.join(x['name'] for x in ability_data))
    else:
        full_description = '\n'.join(ability_data['desc'])
        detail_display = f'''Name: {ability_data['name']}
Full Name: {ability_data['full_name']}
Description: {full_description}
Skills: {', '.join(x['name'] for x in ability_data['skills'])}
'''
        click.echo(detail_display)

@click.command()
@click.argument('skill', required=False, default=None)
def skills(skill):
    skill_data = DND5EAPI.get_skills(skill)
    if skill is None:
        click.echo('\n'.join(x['name'] for x in skill_data))
    else:
        full_description = '\n'.join(skill_data['desc'])
        detail_display = f'''Name: {skill_data['name']}
Description: {full_description}
Ability Score: {skill_data['ability_score']['name']}
'''
        click.echo(detail_display)

@click.command()
@click.argument('char_class', required=False, default=None)
def proficiencies(char_class):
    proficiency_data = DND5EAPI.get_proficiencies(char_class)
    click.echo('\n'.join(x['name'] for x in proficiency_data))


@click.command()
@click.argument('name', required=False, default=None)
def languages(name):
    language_data = DND5EAPI.get_languages(name)
    if name is None:
        click.echo('\n'.join(x['name'] for x in language_data))
    else:
        detail_display = f'''Name: {language_data['name']}
Type: {language_data['type']}
Typical Speakers: {', '.join(language_data['typical_speakers'])}
Script: {language_data['script']}
'''
        click.echo(detail_display)


@click.command()
@click.argument('name', required=False, default=None)
def classes(name):
    class_data = DND5EAPI.get_classes(name)
    if name is None:
        click.echo('\n'.join(x['name'] for x in class_data))
    else:
        proficiency_display = get_class_proficiency_display(class_data)
        equipment_display = get_class_equipment_display(class_data)
        spellcasting_display = get_class_spellcasting_display(class_data)

        detail_display = f'''Name: {class_data['name']}
Hit Die: d{class_data['hit_die']}

Saving Throw Proficiencies: {', '.join(x['name'] for x in class_data['saving_throws'])}
Given Proficiencies: {', '.join(x['name'] for x in class_data['proficiencies'])}
Chosen Proficiencies:
{proficiency_display}

{equipment_display}

Spellcasting:
{spellcasting_display}
'''
        click.echo(detail_display)

def get_class_proficiency_display(class_data):
    if 'proficiency_choices' in class_data:
        proficiency_display = []
        for prof_index, proficiency_choice in enumerate(class_data['proficiency_choices']):
            proficiency_display.append(f'  Option {prof_index + 1} (choose {proficiency_choice["choose"]})')
            if 'from' in proficiency_choice:
                for prof_item in proficiency_choice['from']:
                    proficiency_display.append('    ' + prof_item['name'])
        return '\n'.join(proficiency_display)
    return ''

def get_class_equipment_display(class_data):
    if 'starting_equipment' in class_data:
        equipment_data = class_data['starting_equipment']
        equipment_display = []
        if 'starting_equipment' in equipment_data:
            starting_equip_table = [(x['item']['name'], x['quantity']) 
                                    for x in equipment_data['starting_equipment']]
            equipment_display.append('Starting Equipment:')
            equipment_display.append(get_table_data(starting_equip_table, ['Item', 'Quantity']))
            equipment_display.append('')
        if 'choices_to_make' in equipment_data:
            equipment_display.append('Chosen Equipment:')
            for choice_index in range(1, equipment_data['choices_to_make'] + 1):
                if f'choice_{choice_index}' not in equipment_data:
                    continue
                equipment_display.append(f'  Option {choice_index}:')
                choice_data = equipment_data[f'choice_{choice_index}']
                for choice_item_index, choice_item in enumerate(choice_data):
                    choice_item_type = choice_item['type']
                    choice_item_type = choice_item_type[0].upper() + choice_item_type[1:]
                    equipment_display.append(f'    {choice_item_type} (choose {choice_item["choose"]})')
                    choice_items = [(x['item']['name'], x['quantity']) for x in choice_item['from']]
                    equipment_display.append(get_table_data(choice_items, ['Item', 'Quantity'], indent_level=6))
        return '\n'.join(equipment_display)
    return ''

def get_class_spellcasting_display(class_data):
    if 'spellcasting' in class_data:
        spellcasting_info = class_data['spellcasting']
        spellcasting_display = [
            f'Level: {spellcasting_info["level"]}',
            f'Ability: {spellcasting_info["spellcasting_ability"]["name"]}'
        ]
        for spellcasting_item_info in spellcasting_info['info']:
            spellcasting_display.append(f'- {spellcasting_item_info["name"]}')
            spellcasting_display.append('\n'.join(spellcasting_item_info['desc']))
            spellcasting_display.append('')
        return '\n'.join(spellcasting_display)
    return ''    

@click.command()
@click.argument('char_class', required=False, default=None)
@click.argument('subclass_name', required=False, default=None)
def subclasses(char_class, subclass_name):
    subclass_data = DND5EAPI.get_subclasses(char_class, subclass_name)
    if char_class is not None and subclass_name is not None:
        description_display = '\n'.join(subclass_data['desc'])
        if 'features' in subclass_data:
            features_display = ['Features:']
            for feature in subclass_data['features']:
                features_display.append(f'- {feature["name"]} (level {feature["level"]})')
                features_display.append('  ' + ' '.join(feature['desc']))
            features_display = '\n'.join(features_display)
        else:
            features_display = ''
        
        if 'spells' in subclass_data:
            spells_display = ['Spells:']
            spell_table_data = []
            for spell in subclass_data['spells']:
                spell_name = spell['spell']['name']
                prerequisite = ', '.join(x['name'] for x in spell['prerequisites'])
                acquisition_method = spell['spell_acquisition_method']['name']
                level_acquired = spell['level_acquired']
                spell_table_data.append((spell_name, prerequisite, acquisition_method, level_acquired))
            spells_display.append(get_table_data(spell_table_data, ['Name', 'Prerequisites', 'Acquisition Method', 'Level Acquired']))
            spells_display = '\n'.join(spells_display)
        else:
            spells_display = ''
            
        subclass_display = f'''Name: {subclass_data['name']}
Class: {subclass_data['class']['name']}
Flavor: {subclass_data['subclass_flavor']}
Description: {description_display}

{features_display}

{spells_display}
'''
        click.echo(subclass_display)
    else:
        click.echo('\n'.join(x['name'] for x in subclass_data))

@click.command()
@click.argument('char_class')
@click.argument('char_level', required=False, default=1)
def levels(char_class, char_level):
    level_data = DND5EAPI.get_class_levels(char_class, char_level)
    if 'spellcasting' in level_data:
        spellcasting_info = level_data['spellcasting']
        spellcasting_display = ['Spellcasting:']
        max_spell_slot_level = 0
        for max_spell_slot_iter in range(1, 10):
            if f'spell_slots_level_{max_spell_slot_iter}' in spellcasting_info:
                max_spell_slot_level = max_spell_slot_iter
            else:
                break
        if 'cantrips_known' in spellcasting_info:
            spellcasting_data = [[str(spellcasting_info['cantrips_known']), *(spellcasting_info[f'spell_slots_level_{spell_level}'] for spell_level in range(1, max_spell_slot_level + 1))]]
            spellcasting_columns = ['Cantrips', *(x for x in range(1, max_spell_slot_level + 1))]
        else:
            spellcasting_data = [[spellcasting_info[f'spell_slots_level_{spell_level}'] for spell_level in range(1, max_spell_slot_level + 1)]]
            spellcasting_columns = [x for x in range(1, max_spell_slot_level + 1)]
        spellcasting_display.append(get_table_data(spellcasting_data, spellcasting_columns))
        spellcasting_display = '\n'.join(spellcasting_display)
    else:
        spellcasting_display = ''
    if 'features' in level_data:
        feature_info = level_data['features']
        feature_display = ['Features:']
        for feature in feature_info:
            feature_display.append(f'- {feature["name"]}')
            feature_display.append('  ' + ' '.join(feature['desc']))
        feature_display = '\n'.join(feature_display)
    else:
        feature_display = ''
    if 'class_specific' in level_data:
        class_specific_info = level_data['class_specific']
        class_specific_columns = class_specific_info.keys()
        class_specific_data = [[class_specific_info[x] for x in class_specific_info.keys()]]
        class_specific_display = '\n'.join(['Class Specific:', get_table_data(class_specific_data, class_specific_columns)])
    else:
        class_specific_display = ''

    level_display = f'''Level: {level_data['level']}
Class: {level_data['class']['name']}
Ability Score Bonuses: {level_data['ability_score_bonuses']}
Proficiency Bonus: {level_data['prof_bonus']}

{feature_display}

{spellcasting_display}

{class_specific_display}
'''
    click.echo(level_display)


if __name__ == '__main__':
    cli.add_command(abilities)
    cli.add_command(skills)
    cli.add_command(proficiencies)
    cli.add_command(languages)
    cli.add_command(classes)
    cli.add_command(subclasses)
    cli.add_command(levels)
    cli()

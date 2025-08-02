# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import re


def clean_text(value):
    """Nettoie le texte en supprimant les espaces supplémentaires et les caractères indésirables"""
    if value:
        # Supprimer les balises HTML
        value = remove_tags(value)
        # Supprimer les espaces multiples et les retours à la ligne
        value = re.sub(r'\s+', ' ', value)
        # Supprimer les espaces en début et fin
        value = value.strip()
    return value


def clean_salary(value):
    """Nettoie et normalise les informations de salaire"""
    if value:
        value = clean_text(value)
        # Supprimer les caractères non numériques sauf les chiffres, points, virgules, €, $, k, K
        value = re.sub(r'[^\d\s€$k,.-]', '', value)
        value = value.strip()
    return value


def clean_location(value):
    """Nettoie les informations de localisation"""
    if value:
        value = clean_text(value)
        # Supprimer les parenthèses et leur contenu
        value = re.sub(r'\([^)]*\)', '', value)
        value = value.strip()
    return value


class JobOfferItem(scrapy.Item):
    """Item représentant une offre d'emploi scrapée"""
    
    # Identifiants
    external_id = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Informations principales
    title = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    company = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    location = scrapy.Field(
        input_processor=MapCompose(clean_location),
        output_processor=TakeFirst()
    )
    
    description = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join('\n')
    )
    
    requirements = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join('\n')
    )
    
    # Informations financières
    salary_min = scrapy.Field(
        input_processor=MapCompose(clean_salary),
        output_processor=TakeFirst()
    )
    
    salary_max = scrapy.Field(
        input_processor=MapCompose(clean_salary),
        output_processor=TakeFirst()
    )
    
    salary_currency = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Informations sur l'emploi
    job_type = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    contract_type = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    experience_level = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    remote_work = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # URLs et métadonnées
    url = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    apply_url = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    posted_date = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Dates de traitement
    scraped_at = scrapy.Field()
    processed_at = scrapy.Field()
    
    # Métadonnées de scraping
    scraping_job_id = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    raw_html = scrapy.Field(
        output_processor=TakeFirst()
    )


class CompanyItem(scrapy.Item):
    """Item représentant une entreprise"""
    
    name = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    description = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join('\n')
    )
    
    website = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    industry = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    size = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    location = scrapy.Field(
        input_processor=MapCompose(clean_location),
        output_processor=TakeFirst()
    )
    
    logo_url = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
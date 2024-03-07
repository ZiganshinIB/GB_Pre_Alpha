import random
import requests
from lxml import html
from urllib.parse import urljoin
import config
import re
from pymongo import MongoClient
import time


class HeadHunter:

    root_url = 'https://hh.ru/'

    def __init__(self,collection,
                 User_Agent:str = config.USER_AGENT):
        """
        Инициализация объекта
        :param User_Agent:
        """
        self.headers = {}
        self.collection = collection
        if User_Agent:
            self.headers['User-Agent'] = User_Agent

    def _get_resume_(self, url, **params):
        """
        Собирает данные с конкретной страницы
        :param url: URL адресс
        :param params: параметры
        :return: данные со страницы
        """
        uri = urljoin(self.root_url, url)
        response = requests.get(url=uri, params=params, headers=self.headers)
        if response.status_code != 200:
            print("Что то не так!")
        else:
            tree = html.fromstring(response.content)
            # находим блок с резюме для дальнейшего поиска информации в этом блоке
            try:
                resume = tree.xpath('//div[@class="bloko-gap bloko-gap_top"]')[0]
            except:
                print(tree)
                return None
            data = {}
            try:
                temp = resume.xpath('./div[@data-qa="resume-block-position"]/div[2]/div/div/div/div')[0]
                specializations = ' '.join(temp.xpath('./span/text()'))
                specializations += '| '.join([i.xpath('./text()')[0] for i in temp.xpath('./ul/li')])

                data['specializations'] = specializations
            except Exception:
                data['specializations'] = None
            try:
                data['employment'] = resume.xpath('./div[@data-qa="resume-block-position"]/div[2]/div/div/div/p[1]/text()')[1]
            except:
                data['employment'] = None
            try:
                data['schedule'] = resume.xpath('./div[@data-qa="resume-block-position"]/div[2]/div/div/div/p[2]/text()')[1]
            except:
                data['schedule'] = None

            try:
                data['experience'] = []
                data['text'] = ''
                for exper in resume.xpath('./div[@data-qa="resume-block-experience"]/div[2]/div/div'):
                    experience = {}
                    period = exper.xpath('./div/div[1]/text()')
                    period = period[:4] + exper.xpath('./div/div[1]/span/text()') + period[4:]
                    experience['period'] = (''.join(period))
                    experience['year_'] = 0
                    experience['month_'] = 0
                    for d in exper.xpath('./div/div[1]/div/span'):
                        l = d.xpath('./text()')
                        if l[2] in ['год', 'года', 'лет']:
                            experience['year_'] = int(l[0])
                        if l[2] in ['месяц', 'месяцы', 'месяцев']:
                            experience['month_'] = int(l[0])
                    info = exper.xpath('.//div[@class="resume-block-container"]')[0]
                    data['text'] += f"Работал {experience['period']} ({experience['year_']} г. и {experience['month_']}м.)\n"
                    try:
                        experience['company_name'] = info.xpath('./div[1]//a/text()')[0]
                        data['text'] += f"Название компании {experience['company_name']}"
                    except Exception:
                        temp = info.xpath('./div[1]/text()')
                        if temp:
                            experience['company_name'] = temp[0]
                            data['text'] += f"Название компании {experience['company_name']} "
                        else:
                            experience['company_name'] = None
                    try:
                        experience['city'] = info.xpath('./p/text()')[0]
                        data['text'] += f"город {experience['city']} "
                    except Exception:
                        experience['city'] = None
                    try:
                        experience['position'] = info.xpath('./div[@data-qa="resume-block-experience-position"]/text()')[0]
                        data['text'] += f"на должности {experience['position']}\n"
                    except:
                        experience['position'] = None
                    try:
                        experience['description'] = ''.join(info.xpath('./div[@data-qa="resume-block-experience-description"]/text()'))
                        data['text'] += f"Описание моей работы {experience['description']}\n\n"
                    except Exception:
                        experience['description'] = None

                    data['experience'].append(experience)
                data['text'] += f"\n\r\n"
                data['skils'] = []
                span_skills = resume.xpath('./div[@data-qa="skills-table"]/div[@class="resume-block-item-gap"]//div[@class="bloko-tag-list"]/div/span')
                if span_skills:
                    data['skils'] = [skill.text for skill in span_skills]
                    data['text'] += f"Навыки: {', '.join(data['skils'])} \n"
                try:
                    data['about_me'] = ''.join(resume.xpath('./div[@data-qa="resume-block-skills"]//div[@data-qa="resume-block-skills-content"]/text()'))
                    data['text'] += f"О себе: {data['about_me']}\n"
                except:
                    data['about_me'] = None
                try:

                    div_educations = resume.xpath('./div[@data-qa="resume-block-education"]/div[@class="resume-block-item-gap"]/div/div')
                    data['text'] += f"Образование: \n" if div_educations else "Нет образовании\n"
                    data['educations'] = []
                    for div_education in resume.xpath('./div[@data-qa="resume-block-education"]/div[@class="resume-block-item-gap"]/div/div'):
                        education = {}
                        education['year'] = int(div_education.xpath('./div/div[1]')[0].text)
                        data['text'] += f"\tГод: {education['year']}\n"
                        education['univer'] = div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-name"]')[0].text
                        data['text'] += f"\tУнивер: {education['univer']}\n"
                        education['organization'] = ''.join(div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-organization"]/text()'))
                        data['text'] += f"\tИнформация: {education['organization']}\n"
                        data['educations'].append(education)
                except:
                    data['educations'] = None

                try:
                    div_educations = resume.xpath('./div[@data-qa="resume-block-additional-education"]/div[@class="resume-block-item-gap"]/div/div')
                    data['text'] += f"Повышение квалификации: \n" if div_educations else "Нет квалификации\n"
                    data['additional_educations'] = []
                    for div_education in div_educations:
                        education = {}
                        education['year'] = int(div_education.xpath('./div/div[1]')[0].text)
                        data['text'] += f"\tГод: {education['year']}\n"
                        education['univer'] = div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-name"]')[0].text
                        data['text'] += f"\tУнивер: {education['univer']}\n"
                        education['organization'] = ''.join(div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-organization"]/text()'))
                        data['text'] += f"\tИнформация: {education['organization']}\n"
                        data['additional_educations'].append(education)
                except:
                    data['additional_educations'] = None

                try:
                    div_educations = resume.xpath('./div[@data-qa="resume-block-attestation-education"]/div[@class="resume-block-item-gap"]/div/div')
                    data['text'] += f"Экзамены: \n" if div_educations else "Нет сдавал экзамены\n"
                    data['attestation_educations'] = []
                    for div_education in div_educations:
                        education = {}
                        education['year'] = int(div_education.xpath('./div/div[1]')[0].text)
                        data['text'] += f"\tГод: {education['year']}\n"
                        education['univer'] = div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-name"]')[0].text
                        data['text'] += f"\tУнивер: {education['univer']}\n"
                        education['organization'] = ''.join(div_education.xpath('./div/div[2]//div[@data-qa="resume-block-education-organization"]/text()'))
                        data['text'] += f"\tИнформация: {education['organization']}\n"
                        data['attestation_educations'].append(education)
                except:
                    data['attestation_educations'] = None
            except Exception:
                data['experience'] = []
            return data

    def get_resumes_page(self, params):
        '''
        Собирает 20 данных приведенных на странице
        :return:
        '''
        url = 'search/resume'
        uri = urljoin(self.root_url, url)
        response = requests.get(url=uri, params=params, headers=self.headers)
        if response.status_code != 200:
            print("Что то не так!")
            return
        else:
            tree = html.fromstring(response.content)
            resumes = tree.xpath('//div[@data-qa="resume-serp__resume"]')

            datas = []
            for resume in resumes:
                data = {}
                res = resume.xpath("./div")
                data['update_date'] = str(''.join(res[0].xpath("./div/div/div/span[2]/span/span/text()")))
                res_inf = res[0].xpath('./div/h3[1]/span/a')
                data['resume_url'] = re.match(r"^\/\w*\/\w*", res_inf[0].get('href')).group(0)
                data['resume_title'] = res_inf[0].xpath('./span/text()')[0]
                try:
                    data['age'] = int(res[0].xpath('.//span[@data-qa="resume-serp__resume-age"]/span/text()')[0])
                except Exception:
                    data['age'] = None
                try:
                    data['salary'] = int(res[0].xpath('./div/div[5]/div/text()')[0].replace('\u2009',''))
                except Exception:
                    data['salary'] = None
                try:
                    data['currency'] = res[0].xpath('./div/div[5]/div/text()')[-1]
                except:
                    data['currency'] = None
                try:
                    data["status"] = res[0].xpath('./div/div[7]/div/text()')[0]
                except Exception:
                    data['status'] = None
                try:
                    data['experience_year'] =int(res[0].xpath('./div[3]/div[1]/div/div[2]/span[1]/text()')[0])
                except:
                    data['experience_year'] = None
                try:
                    data['experience_month'] =int(res[0].xpath('./div[3]/div[1]/div/div[2]/span[2]/text()')[0])
                except:
                    data['experience_month'] = None
                advance_data = self._get_resume_(url= data['resume_url'])
                if advance_data:
                    data = data | advance_data
                    self.collection.insert_one(data)
                else:
                    time.sleep(3)
                    print("Error")
                # Обойдемся без DOS-атаки, random что бы не сразу поняли что мы берем данные
                time.sleep(1+random.random()*3)

    def all_get_resumes(self, find):
        """
        Автоматический переходит по всем страницам и собираем данне
        :return:
        """
        for i in range(250):
            params = f'text={find}&ored_clusters=true&order_by=relevance&search_period=0&logic=normal&pos=full_text&exp_period=all_time&page={i}'
            self.get_resumes_page(params)
            time.sleep(3+random.random()*3)


if __name__ == "__main__":
    host = '192.168.96.96'
    port = 27017
    user_name = 'MongoAdmin'
    password = 'mongo123'
    try:
        mongo = MongoClient(f'mongodb://{user_name}:{password}@{host}:{port}/')
        dataBase = mongo.client['hh_gb']
        collection = dataBase.db['hh']
        hh = HeadHunter(collection)
        hh.all_get_resumes(find="1с+программист")
    except:
        print("Нет связи с Базой данных ")
        print(f"Проверти сервер {host}, если работает то проверти контейнер командой\ndocker ps")







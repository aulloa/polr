import base64
from flask import Flask
from flask import request
from flask import send_from_directory
import itertools
from lxml import html
import matplotlib
matplotlib.use('Agg')
import matplotlib.cm
import matplotlib.pyplot
import numpy
import pandas
import requests
import StringIO


app = Flask(__name__)


@app.route('/')
def main():
    skills = request.args.get('POLR')
    if skills is not None:
        basic_skills = skills.split(" ")[:20]
        raw_skill_sets = make_raw_skill_sets(basic_skills)
        list_of_meta_skill_sets = map(MetaSkillSet, raw_skill_sets)
        for meta_skill_set in list_of_meta_skill_sets:
            meta_skill_set.get_meta_data()
        top_skill_sets = get_top_skill_sets(list_of_meta_skill_sets, 20)
        salaries = [meta_skill_set.salary / 1000 for meta_skill_set in top_skill_sets]
        skill_set_names = [meta_skill_set.skill_set for meta_skill_set in top_skill_sets]
        list_of_number_of_jobs = [meta_skill_set.number_of_jobs for meta_skill_set in top_skill_sets]
        salary_plot = salary_by_skill_set_plot(salaries, skill_set_names)
        center_style = 'text-align:center;'
        html_output = '<p style="{}"><img src="data:image/png;base64,{}"  style="width:900px;height:450px;"></p>'
        salary_html = html_output.format(center_style, salary_plot)
        num_jobs_plot = number_of_jobs_by_skill_set(list_of_number_of_jobs, skill_set_names)
        num_jobs_html = html_output.format(center_style, num_jobs_plot)
        cc_plot = color_coded_salaries_by_skill_set(salaries, skill_set_names, list_of_number_of_jobs)
        cc_html = html_output.format(center_style, cc_plot)
        output = salary_html + num_jobs_html + cc_html + AD
        return output
    else:
        return send_from_directory('static', 'front_page.html')

FIGSIZE = (50, 15)

AD = '<p style = "position: relative; bottom: 0; width:100%; text-align: center">' \
        'Like what you see?, Support the dev, click on an ad:<P>' \
        '<script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>' \
        '<!-- SkillsAd -->' \
        '<ins class="adsbygoogle"' \
        'style="display:block"' \
        'data-ad-client="ca-pub-3214118222399516"' \
        'data-ad-slot="9247590985"' \
        'data-ad-format="auto"></ins>' \
        '<script>' \
        '(adsbygoogle = window.adsbygoogle || []).push({});' \
        '</script>'


def make_raw_skill_sets(skills):
    """makes a list of every combination of skills in a skills list maximum 4

    Should be read : add all combinations of a certain size to a list for every possible size in the
    the list_of_things.

    """

    possible_sizes_in_list_of_things = range(4)
    basic_skills = [list(combinations_of_a_certain_size)
                    for each_possible_size_of_combination in possible_sizes_in_list_of_things
                    for combinations_of_a_certain_size in itertools.combinations(skills,
                                                                                 each_possible_size_of_combination)]

    return basic_skills


class MetaSkillSet(object):
    """gets extra data concerning a skillset

    Attributes
    ----------
    skill_set : list
        a specific list of skills
    payload : dict
        REST terms used to specify jobs to return
    page : html page
        html page returned by job search
    salary : float
        a weighted average of salaries for the number of jobs in a skillset
    number_of_jobs : float
        the number of job postings for skillset
    """

    def __init__(self, skill_set):
        """
        Params
        ------
        skill_set : list
        """
        self.skill_set = skill_set
        self.payload = None
        self.page = None
        self.salary = None
        self.number_of_jobs = None

    def get_meta_data(self):
        self.skills_to_payloads()
        self.request_html_page()
        self.skills_to_salary()

    def skills_to_payloads(self):
        """takes self.skill_set and turns them into payloads for get requests and sets self.payload

        Note
        ----
        payloads : list
            payloads contain a list of dictionaries which represent the parameters used to specify jobs and restrictions

        """
        if isinstance(self.skill_set, str):
            query = self.skill_set
        else:
            query = ' '.join(self.skill_set)
        payload = {'q': query,
                   'l': ''}
        self.payload = payload

    def request_html_page(self):
        """sets self.page to html page

        Note
        ----
        response.content : html page
            the html page returned by requests
        """
        try:
            response = requests.get('http://www.indeed.com/jobs?', params=self.payload)
        except:
            print "got error for ", self.payload
        self.page = response.content

    def skills_to_salary(self):
        """sets self.salary and self.number of jobs to weighted salary and number of jobs

        Note
        ----
        weighted_average_salary : float
            a weighted average of salaries for the number of jobs in the objects skillset
        number_of_jobs : float
            the number of job postings for skillset
        """
        tree = html.fromstring(self.page)
        numerator = []
        denominator = []
        for salary in range(1, 6):
            salary_x_path = '//*[@id="SALARY_rbo"]/ul/li[' + str(salary) + ']/a/text()'
            number_of_jobs_x_path = '//*[@id="SALARY_rbo"]/ul/li[' + str(salary) + ']/text()'
            salary_str = tree.xpath(salary_x_path)
            num_of_jobs_str = tree.xpath(number_of_jobs_x_path)
            try:
                salary_float = float(salary_str[0].strip("$, +").replace(',', ''))
                num_of_jobs_float = float(num_of_jobs_str[1].strip("( , )"))
            except IndexError:
                salary_float = 0
                num_of_jobs_float = 1
            numerator.append(salary_float * num_of_jobs_float)
            denominator.append(num_of_jobs_float)
        weighted_average_salary = sum(numerator) / sum(denominator)
        total_number_of_jobs = sum(denominator)
        self.salary = weighted_average_salary
        self.number_of_jobs = total_number_of_jobs


def get_top_skill_sets(meta_skill_sets, n):
    meta_skill_sets.sort(key=lambda x: x.salary, reverse=True)
    top_skills = meta_skill_sets[0:n]
    return top_skills


def salary_by_skill_set_plot(salaries, skill_set_names):
    """plots a list of meta skill sets salary by skill set"""
    data_frame = pandas.DataFrame({'skill_set': skill_set_names,
                                   'salary': salaries
                                   })
    plot = data_frame.plot(kind="bar", x=data_frame['skill_set'],
                           title="Salary by SkillSet",
                           legend=False,
                           figsize=FIGSIZE,
                           fontsize=40,
                           grid=True)
    plot.set_title("Salary by SkillSet", fontsize=40)
    plot.set_xlabel("SkillSet", fontsize=40)
    plot.set_ylabel("Salary (1000 USD)", fontsize=40)
    fig = plot.get_figure()
    fig.tight_layout()
    figfile = StringIO.StringIO()
    fig.savefig(figfile, format='png')
    encoded_fig_file = base64.b64encode(figfile.getvalue())
    return encoded_fig_file


def number_of_jobs_by_skill_set(number_of_jobs, skill_set_names):
    """plots a list of meta skill sets number of jobs by skill set"""
    data_frame = pandas.DataFrame({'skill_set': skill_set_names,
                                   'salary': number_of_jobs
                                   })
    plot = data_frame.plot(kind="bar", x=data_frame['skill_set'],
                           title="number of jobs by SkillSet",
                           legend=False,
                           figsize=FIGSIZE,
                           fontsize=28,
                           grid=True)
    fig = plot.get_figure()
    fig.tight_layout()
    plot.set_title("Number of jobs for SkillSets", fontsize=40)
    plot.set_xlabel("SkillSet", fontsize=40)
    plot.set_ylabel("Number of Jobs", fontsize=40)
    fig = plot.get_figure()
    fig.tight_layout()
    figfile = StringIO.StringIO()
    fig.savefig(figfile, format='png')
    encoded_fig_file = base64.b64encode(figfile.getvalue())
    return encoded_fig_file


def color_coded_salaries_by_skill_set(salaries, skill_sets, number_of_jobs_list):
    """plots salaries by skill sets with color indicating number of jobs

    Parameters
    ----------
    salaries :
    skill_sets :

    Returns
    -------

    """
    x = numpy.arange(len(salaries))
    labels = skill_sets
    width = 0.5
    highest_job_count = max(number_of_jobs_list)
    colors = [matplotlib.cm.Blues(number_of_jobs / highest_job_count) for number_of_jobs in number_of_jobs_list]
    matplotlib.pyplot.figure(figsize=FIGSIZE)
    matplotlib.pyplot.bar(x, salaries, width=width, color=colors)
    matplotlib.pyplot.colors()
    matplotlib.pyplot.xticks(x + width / 2, labels, rotation='vertical')
    matplotlib.pyplot.xlim(0, x[-1] + width * 2)
    matplotlib.pyplot.title("Salaries Color Coded", fontsize=40)
    matplotlib.pyplot.gca().get_xaxis().tick_bottom()
    matplotlib.pyplot.gca().get_yaxis().tick_left()
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.xlabel("SkillSet", fontsize=40)
    matplotlib.pyplot.ylabel("Salary (1000 USD)", fontsize=40)
    matplotlib.pyplot.tick_params(labelsize=40)
    matplotlib.pyplot.tight_layout()
    figfile = StringIO.StringIO()
    matplotlib.pyplot.savefig(figfile, format='png')
    encoded_fig_file = base64.b64encode(figfile.getvalue())
    return encoded_fig_file

if __name__ == '__main__':
    app.run()

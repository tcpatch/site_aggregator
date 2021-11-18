from django.shortcuts import render

from django.http import HttpResponse
from urllib.request import urlopen
import xml.etree.ElementTree as xml
import xml.etree.ElementTree as ET


def index(request):
    html = main()
    context = {'compiled': html}
    return render(request, 'aggregator/index.html', context)


def get_celtics_content():
    with urlopen('https://www.celticsblog.com/rss/current.xml') as xml_request:
        xml_lines = xml_request.readlines()
        # all_lines = ''.join([str(i) for i in xml_lines])
        # rootElement = xml.parse(tree)
        # rootElement = tree.getroot()
    html_content = list()
    titles = list()
    stories = list()
    add_lines = False
    for binary_l in xml_lines:
        l = str(binary_l).strip().replace("b'", '', 1).replace("\\n'", '').replace("\\xe2\\x80\\x99", "'")
        if '<title>' in l and 'CelticsBlog -  All Posts' not in l:
            titles.append(l.replace('title', 'h1'))
        if '<content' in l:
            add_lines = True
            # html_content.append(l)
        if '</content>' in l:
            add_lines = False
            # html_content.append(l)
            stories.append(''.join(html_content))
            html_content = list()
        if add_lines:
            html_content.append(l.replace('&lt;', '<')
                                .replace('&gt;', '>')
                                .replace('\\xe2\\x80\\x99', "'")
                                .replace('\\xe2\\x80\\x9c', '<span style="font-style: italic;">')
                                .replace('\\xe2\\x80\\x9d', '</span>'))
    assert len(titles) == len(stories)
    compiled_html = ''
    for i, j in zip(titles, stories):
        compiled_html += i
        compiled_html += '\n'
        compiled_html += j
    return compiled_html

    # with open('test.html', 'w') as fp:
    #     for i, j in zip(titles, stories):
    #         fp.write(i)
    #         fp.write('\n')
    #         fp.write(j)


def get_weather():
    url = 'https://forecast.weather.gov/MapClick.php?lat=42.47641470000008&lon=-71.47551399999998#.YYx99upOlH5'
    with urlopen(url) as xml_request:
        xml_lines = [str(i).replace("b'", '', 1).replace("\\n'", '') for i in xml_request.readlines()]
    compiled_dict = {'current': [],
                     'seven': [],
                     'detailed': []}
    write_to = None
    div_count = 0
    end_div_count = 0
    for l in xml_lines:
        if l.strip().startswith('<div id="current-conditions"'):
            write_to = 'current'
        elif l.strip().startswith('<div id="seven-day-forecast"'):
            write_to = 'seven'
        elif l.strip().startswith('<div id="detailed-forecast"'):
            write_to = 'detailed'
        if write_to:
            compiled_dict[write_to].append(l.replace('\\t', '&#9;')
                                            .replace('src="newimages', 'src="https://forecast.weather.gov/newimages')
                                            .replace('src="DualImage.php', 'src="https://forecast.weather.gov/DualImage.php'))
            end_div_count += l.count('</div>')
            div_count += l.count('<div')
            if div_count == end_div_count:
                write_to = False
                div_count = 0
                end_div_count = 0
    final_html = '<link rel="stylesheet" type="text/css" href="weather_style.css">\n'
    for k in compiled_dict:
        final_html += ''.join(compiled_dict[k])
    return final_html
    # with open('weather_test.html', 'w') as fp:
    #     fp.write(final_html)


def get_ycombinator():
    url = 'https://news.ycombinator.com/rss'
    with urlopen(url) as xml_request:
        tree = ET.parse(xml_request)
        root = tree.getroot()
    summary_list = list()
    for child in root[0]:
        sub_dict = {'title': '',
                    'link': '',
                    'description': ''}
        for c in child:
            if c.tag in sub_dict:
                sub_dict[c.tag] = c.text
        if not sub_dict['link']:
            continue
        summary_list.append('<div><a href="{}">{}</a> ({}) {}</div>'.format(sub_dict['link'],
                                                                       sub_dict['title'],
                                                                       sub_dict['link'].replace('https://', '').replace('http://', '').split('/')[0],
                                                                       sub_dict['description']))
    return '\n'.join(summary_list)


def get_krebs():
    # TODO this can become it's own function - duplicating get_ycombinator()
    url = 'https://krebsonsecurity.com/rss'
    with urlopen(url) as xml_request:
        tree = ET.parse(xml_request)
        root = tree.getroot()
    summary_list = list()
    for child in root[0]:
        if child.tag == 'item':
            sub_dict = {'title': '',
                        'link': '',
                        'description': ''}
            for c in child:
                if c.tag in sub_dict:
                    sub_dict[c.tag] = c.text
            summary_list.append('<div><a href="{}">{}</a> {}</div>'.format(sub_dict['link'],
                                                                        sub_dict['title'],
                                                                        sub_dict['description']))
    return '\n'.join(summary_list)


def parse_xml(url, tags):
    # TODO see common `get_krebs` and `get_ycombinator`...
    raise NotImplementedError

def main():
    celtics_html = get_celtics_content()
    weather_html = get_weather()
    ycomb_html = get_ycombinator()
    krebs_html = get_krebs()
    start_dropdown = '<div>\n<div class="customHeading" data-section="{}" onclick="toggleShow(event)"> {}:</div>\n<div id="{}" class="hide">\n'
    end_dropdown = '</div>\n</div>\n'
    show_hide_function = '<script type="text/javascript">function toggleShow(e){toggleThis = event.target.dataset.section;toggleElement = document.getElementById(toggleThis);if (toggleElement.className == "show") {toggleElement.className = "hide";} else {toggleElement.className = "show";}};</script>\n'
    final_html = ''
    for i in [['celtics', 'Celtics Blog', celtics_html],
              ['ycomb', 'YCombinator News', ycomb_html],
              ['krebs', 'Krebs On Security', krebs_html],
              ['weather', 'Acton Weather', weather_html]]:
        final_html += start_dropdown.format(i[0], i[1], i[0])
        print(start_dropdown.format(i[0], i[1], i[0]))
        final_html += i[2]
        final_html += end_dropdown
    final_html += show_hide_function
    return final_html

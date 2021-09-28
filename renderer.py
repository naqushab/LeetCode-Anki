import random
import re

from genanki import Model, Deck, Note, Package
from markdown import markdown

from database import Problem
from utils import parser as conf

if conf.get("Config", "company_mode") == "True":
    card_name = conf.get("Config", "company")
else:
    card_name = 'Leetcode'


def random_id():
    return random.randrange(1 << 30, 1 << 31)


def markdown_to_html(content: str):
    # replace the math symbol "$$x$$" to "\(x\)" to make it compatible with mathjax
    content = re.sub(
        pattern=r"\$\$(.*?)\$\$",
        repl=r"\(\1\)",
        string=content
    )

    # also need to load the mathjax and toc extensions
    return markdown(content, extensions=['mdx_math', 'toc', 'fenced_code', 'tables'])


def code_to_html(source, language):
    content = f"```{language}\n{source}\n```"
    return markdown(content, extensions=['fenced_code'])


def get_anki_model():
    with open(conf.get("Anki", "front"), 'r') as f:
        front_template = f.read()
    with open(conf.get("Anki", 'back'), 'r') as f:
        back_template = f.read()
    with open(conf.get("Anki", 'css'), 'r') as f:
        css = f.read()

    anki_model = Model(
        model_id=1048217874,
        name=card_name,
        fields=[
            {"name": "ID"},
            {"name": "Title"},
            {"name": "TitleSlug"},
            {"name": "Difficulty"},
            {"name": "Description"},
            {"name": "Tags"},
            {"name": "TagSlugs"},
            {"name": "CompanyTags"},
            {"name": "CompanyTagSlugs"},
            {"name": "Solution"},
            {"name": "Submission"}
        ],
        templates=[
            {
                "name": card_name,
                "qfmt": front_template,
                "afmt": back_template
            }
        ],
        css=css
    )
    return anki_model


def make_note(problem):
    print(f"📓 Producing note for problem: {problem.title}...")
    tags = ";".join([t.name for t in problem.tags])
    tags_slug = ";".join([t.slug for t in problem.tags])
    company_tags = ";".join([t.name for t in problem.company_tags])
    company_tags_slug = ";".join([t.slug for t in problem.company_tags])

    try:
        solution = problem.solution.get()
    except Exception:
        solution = None

    codes = []
    for item in problem.submissions:
        source = item.source.encode().decode("unicode-escape")
        output = code_to_html(source, item.language)
        codes.append(output)
    submissions = "\n".join(codes)

    note = Note(
        model=get_anki_model(),
        fields=[
            str(problem.display_id),
            problem.title,
            problem.slug,
            problem.level,
            problem.description,
            tags,
            tags_slug,
            company_tags,
            company_tags_slug,
            markdown_to_html(solution.content) if solution else "",
            submissions
        ],
        guid=str(problem.display_id),
        sort_field=str(problem.display_id),
        tags=[t.slug for t in problem.tags] + [t.slug for t in problem.company_tags]
    )
    return note


def render_anki():
    problems = Problem.select().order_by(
        Problem.display_id
    )

    anki_deck = Deck(
        deck_id=random_id(),
        name=card_name
    )

    for problem in problems:
        note = make_note(problem)
        anki_deck.add_note(note)

    path = conf.get("Anki", "output") + f'{card_name}.apkg'
    Package(anki_deck).write_to_file(path)


if __name__ == '__main__':
    render_anki()

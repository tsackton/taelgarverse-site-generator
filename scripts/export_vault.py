import shutil
import yaml
import json
import re
import os
from datetime import datetime
from pathlib import Path
from slugify import slugify

###############################
####### CONSTANTS #############
###############################

# For Regex, match groups are:
#       0: Whole roamlike link e.g. [[filename#title|alias|widthxheight]]
#       1: Filename e.g. filename.md
#       2: #title
#       3: alias
#       4: width
#       5: height
WIKILINK_RE = r"""\[\[(.*?)(\#.*?)?(?:\|([\D][^\|\]]+[\d]*))?(?:\|(\d+)(?:x(\d+))?)?\]\]"""

# words always lowercase in titles
EXCLUSIONS = ['A', 'An', 'The', 'And', 'But', 'Or', 'For', 'Nor', 'As', 'At', 'By', 'For', 'From', 'In', 'Into', 'Near', 'Of', 'On', 'Onto', 'To', 'With', 'De', 'About']
ALWAYS_UPPPER = ['DR']

################################
##### FUNCTIONS - MAY MOVE #####
################################

# Custom dumper for handling empty values
class CustomDumper(yaml.SafeDumper):
    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

# Add custom representation for None (null) values
CustomDumper.add_representer(type(None), CustomDumper.represent_none)

class MkDocsNavigationGenerator:
    def __init__(self, template_path, file_frontmatter, docs_dir, exclude_tildes=True):
        self.template_path = template_path
        self.file_frontmatter = file_frontmatter
        self.exclude_tildes = exclude_tildes
        self.source_dir = Path(docs_dir)

    @staticmethod
    def count_indentation(line):
        """ Count the number of leading spaces or tabs to determine the depth """
        return (len(line) - len(line.lstrip(' '))) // 4  # Assuming 4 spaces per indentation level

    def generate_markdown_list_from_directory(self, directory, depth=0, exclude_files=None):
        """ Generate markdown list entries from a directory based on file_frontmatter info """
        markdown_list = []
        indent = '    ' * depth  # 4 spaces for each level of nesting

        full_path = self.source_dir / Path(directory)
        if not exclude_files:
            exclude_files = []

        # Separate files and subdirectories
        files = [item for item in full_path.glob("*.md") if item.is_file() and item.name not in exclude_files]
        subdirs = [item for item in full_path.iterdir() if item.is_dir()]

        # Process files
        for file_path in sorted(files, key=lambda x: self.file_frontmatter.get(x.stem, {}).get('title', '').lower()):
            file_display_path = file_path.relative_to(self.source_dir)
            title = self.file_frontmatter.get(file_path.stem, {}).get('title', '~Unnamed~')
            if title.startswith("~") and self.exclude_tildes:
                continue
            markdown_list.append(f"{indent}- [{title}]({file_display_path})")

        # Process subdirectories
        for subdir in sorted(subdirs, key=lambda x: x.name.lower()):
            subdir_path = subdir.relative_to(self.source_dir)
            index_file = subdir_path / f"{subdir.name}.md"

            if (self.source_dir / index_file).is_file() and index_file.stem in self.file_frontmatter:
                title = self.file_frontmatter[index_file.stem].get('title', title_case(subdir.stem.replace("-", " ")))
                markdown_list.append(f"{indent}- [{title}]({index_file})")
            else:
                # title case subdir name
                subdir = title_case(subdir.name.replace("-", " "))
                markdown_list.append(f"{indent}- {subdir}")
            markdown_list.extend(self.generate_markdown_list_from_directory(subdir_path, depth + 1, exclude_files=exclude_files))

        return markdown_list

    def process_template(self):
        """ Process the template file and replace glob patterns with generated markdown lists """
        processed_lines = []

        with open(self.template_path, 'r') as template_file:
            for line in template_file:
                if '{glob:' in line:
                    # Extract directory path, calculate depth, and parse optional exclude pattern
                    parts = line.split(',')
                    dir_path = parts[0].split('{glob:')[-1].strip().replace('}', '')
                    exclude_files = None
                    if len(parts) > 1 and 'exclude:' in parts[1]:
                        exclude_files = parts[1].split('exclude:')[-1].strip().strip('}').split(";")
                    depth = self.count_indentation(line)
                    processed_lines.extend(
                        self.generate_markdown_list_from_directory(
                            dir_path, depth, exclude_files=exclude_files
                        )
                    )
                else:
                    processed_lines.append(line.rstrip())

        return processed_lines



class WikiLinkReplacer:
    """
    Adapted from  https://github.com/Jackiexiao/mkdocs-roamlinks-plugin
    """
    def __init__(self, base_docs_url, page_url, path_dict, slug):
        self.base_docs_url = base_docs_url
        self.page_url = page_url
        self.path_dict = path_dict
        self.slug = slug

    def simplify(self, filename):
        """ ignore - _ and space different, replace .md to '' so it will match .md file,
        if you want to link to png, make sure you filename contain suffix .png, same for other files
        but if you want to link to markdown, you don't need suffix .md """
        return re.sub(r"[\-_ ]", "", filename.lower()).replace(".md", "")

    def gfm_anchor(self, title):
        """Convert to gfw title / anchor
        see: https://gist.github.com/asabaylus/3071099#gistcomment-1593627"""
        if title:
            title = title.strip().lower()
            title = re.sub(r'[^\w\u4e00-\u9fff\- ]', "", title)
            title = re.sub(r' +', "-", title)
            return title
        else:
            return ""

    def __call__(self, match):
        # Name of the markdown file
        whole_link = match.group(0)
        filename = match.group(1).strip() if match.group(1) else ""
        title = match.group(2).strip() if match.group(2) else ""
        format_title = self.gfm_anchor(title)
        alias = match.group(3) if match.group(3) else ""
        width = match.group(4) if match.group(4) else ""
        height = match.group(5) if match.group(5) else ""

        # Absolute URL of the linker
        abs_linker_url = os.path.dirname(
            os.path.join(self.base_docs_url, self.page_url))

        # Find directory URL to target link
        rel_link_url = ''
        # Walk through all files in docs directory to find a matching file
        if filename:
            if filename in self.path_dict:
                alias = str(filename) if alias == "" else alias
                if slugify_files:
                    filename = str(self.path_dict[filename]['file'])
                else:
                    filename = str(self.path_dict[filename]['orig'])
            else:
                ## check to see if we have a broken obsidian path
                # this is not the best way to do this
                parts = filename.split('/')
                if parts[-1] in self.path_dict:
                    alias = str(parts[-1]) if alias == "" else alias
                    if slugify_files:
                        filename = str(self.path_dict[parts[-1]]['file'])
                    else:
                        filename = str(self.path_dict[parts[-1]]['orig'])
            if "http://" in filename or "https://" in filename:
                rel_link_url = filename
            else:
                if os.path.sep in filename:
                    rel_file = filename
                    if not '.' in filename:   # don't have extension type
                        rel_file = filename + ".md"

                    abs_link_url = os.path.dirname(os.path.join(
                        self.base_docs_url, rel_file))
                    # Constructing relative path from the linker to the link
                    rel_link_url = os.path.join(
                            os.path.relpath(abs_link_url, abs_linker_url), os.path.basename(rel_file))
                    if title:
                        rel_link_url = rel_link_url + '#' + format_title
                else:
                    for root, dirs, files in os.walk(self.base_docs_url, followlinks=True):
                        for name in files:
                            # If we have a match, create the relative path from linker to the link
                            if self.simplify(name) == self.simplify(filename):
                                # Absolute path to the file we want to link to
                                abs_link_url = os.path.dirname(os.path.join(
                                    root, name))
                                # Constructing relative path from the linker to the link
                                rel_link_url = os.path.join(
                                        os.path.relpath(abs_link_url, abs_linker_url), name)
                                if title:
                                    rel_link_url = rel_link_url + '#' + format_title
            if rel_link_url == '':
                # print(f"Cannot find {filename} in directory {self.base_docs_url}")
                if alias:
                    return alias
                else:
                    if not "." in filename:
                        return filename
                    else:
                        return whole_link
        else:
            rel_link_url = '#' + format_title

        # Construct the return link
        # Windows escapes "\" unintentionally, and it creates incorrect links, so need to replace with "/"
        rel_link_url = rel_link_url.replace("\\", "/")

        # define image link as: filename has is xxx.png, xxx.jpg, xxx.jpeg, xxx.gif, or alias = right or left, or width or height is not empty
        image_link = re.search(r".*\.(png|jpg|jpeg|gif)$", filename) or alias in ["right", "left"] or width or height

        if image_link:
            # alias becomes align = right or left
            # width and height becomes width and height
            # convert -_ to space in filename, remove extension, and title case for alias
            alignment = f'align="{alias}"' if alias in ["right", "left"] else ""
            width = f'width="{width}"' if width else ""
            height = f'height="{height}"' if height else ""
            alias = title_case(Path(filename).stem.replace("-", " ").replace("_", " "))
            if alignment or width or height:
                image_params = "{" + "; ".join([param for param in [alignment, width, height] if param]) + "}"
            else:
                image_params = ""
            link = f'[{alias}]({rel_link_url}){image_params}'
                               
        else:
            if filename:
                if alias:
                    link = f'[{alias}](<{rel_link_url}>)'
                else:
                    link = f'[{filename+title}](<{rel_link_url}>)'
            else:
                if alias:
                    link = f'[{alias}](<{rel_link_url}>)'
                else:
                    link = f'[{title}](<{rel_link_url}>)'

        return link


def title_case(s, exclusions=None, always_upper=None):
    if exclusions is None:
        exclusions = []

    if always_upper is None:
        always_upper = []

    # Convert exclusions to lowercase for case-insensitive comparison
    exclusions = [word.lower() for word in exclusions]
    # Keep always_upper as it is for exact matching

    words = s.split()
    title_cased_words = []

    for i, word in enumerate(words):
        # Remove punctuation for comparison, but retain original for replacement
        word_stripped = re.sub(r'\W+', '', word)

        # Check if the stripped word (case-insensitive) is in always_upper
        if any(word_stripped.lower() == au.lower() for au in always_upper):
            # Preserve original non-word characters, capitalize the rest
            title_cased_words.append(word.upper())
        elif i == 0 or word_stripped.lower() not in exclusions:
            # Capitalize the first unicode character that is a letter
            title_cased_words.append(re.sub(r'(\b\w)', lambda x: x.groups()[0].upper(), word, 1))
        else:
            # If in exclusions, keep the word as it is
            title_cased_words.append(word.lower())

    return ' '.join(title_cased_words)

def parse_markdown_file(file_path):
    """
    Reads a markdown file and returns its frontmatter as a dictionary and the rest of the text as a string.

    :param file_path: Path to the markdown file.
    :return: A tuple containing a dictionary of the frontmatter and a string of the markdown text.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content at the triple dashes
    parts = content.split('---')

    # Check if there is frontmatter
    if len(parts) < 3:
        return {}, content

    frontmatter = yaml.safe_load(parts[1])  # Parse the frontmatter
    markdown_text = '---'.join(parts[2:])   # Join back the remaining parts

    return frontmatter, markdown_text

def strip_comments(s):
    """
    Takes a string as input, and strips all text between %% markers, or between a %% and EOF if there is an unmatched %%.
    Properly handles nested comments - strips only from %% to the next %%.
    Additionally, it handles cases where there is an unmatched %% by removing everything from that %% to the end of the file.
    """
    return re.sub(r'%%.*?%%|%%.*', '', s, flags=re.DOTALL)

def strip_campaign_content(s, text):
    """
    Given a string s, it finds strings of the format:
    %%^Campaign:text%%
    some text here
    %%^End%%
    It keeps all text between %%^Campaign:text%% and %%^End%% if the argument text matches the text in the %% line, 
    and removes it otherwise.
    """
    # This function will be used to determine whether to keep or remove the matched text
    def keep_or_remove(match):
        campaign_text = match.group(1)
        content = match.group(2)
        return content if text.lower() == campaign_text.lower() else ""

    pattern = r'%%\^Campaign:(.*?)%%(.*?)%%\^End%%'
    return re.sub(pattern, keep_or_remove, s, flags=re.DOTALL | re.IGNORECASE)

def parse_date(date_str):
    """
    Tries to parse the date string in various formats and returns a datetime object.
    """
    for fmt in ['%Y', '%Y-%m', '%Y-%m-%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date '{date_str}' is not in a recognized format")

def strip_date_content(s, input_date_str):
    """
    Removes text between %%^Date:YYYY-MM-DD%% and %%^End%% if the input_date is before the date in the %% comment.
    The date in the comment and the input date can be in the formats YYYY, YYYY-MM, or YYYY-MM-DD.
    """
    # Convert input_date_str to datetime
    input_date = parse_date(input_date_str)

    def replace_func(match):
        # Extract the date from the comment
        comment_date_str = match.group(1)
        # Parse the comment date
        comment_date = parse_date(comment_date_str)

        # Compare the dates
        if input_date < comment_date:
            return ""  # Remove the text if input_date is before comment_date
        else:
            return match.group(0)  # Keep the text otherwise

    # Define the regular expression pattern
    pattern = r'%%\^Date:(.*?)%%(.*?)%%\^End%%'
    # Replace matching sections
    return re.sub(pattern, replace_func, s, flags=re.DOTALL)

def build_md_list(path, keep_only_rooted=False):
    """
    Given a path, makes a dictionary of all the markdown files in the path.
    The dictionary has the original file name as the key, and a dict with two keys as the value:
    - 'file' contains the slugified file name
    - 'path' contains the path relative to the source directory to the file, with slugified directories
    """

    md_files = {}

    for file in path.rglob('*'):
        # skip files that start with a dot or underscore; will eventually fix this to a true ignore list
        if not any(part.startswith('.') for part in file.parts) and not any(part.startswith('_') for part in file.parts):
            
            # skip if directory
            if file.is_dir():
                continue

            # get the original file name, without md if present
            orig_file_name = file.stem + "".join(suffix_part for suffix_part in file.suffixes if suffix_part != ".md")

            # get the slugified file name
            slug_file_name = slugify(file.stem) + "".join(file.suffixes)

            # check if the file is a markdown file
            process = True if file.suffix == '.md' and len(file.suffixes) == 1 else False

            if slug_file_name in md_files:
                raise ValueError(f"Duplicate file basename found: {file}\n", md_files[slug_file_name])

            # get the relative path to the file, relative to source
            relative_path_parents = str(file.relative_to(path).parent).split(os.path.sep)

            # slugified full path
            slug = Path(*[slugify(part) for part in relative_path_parents]) / slug_file_name
            orig = file.relative_to(path).parent / file.name

            # get text and frontmatter
            add_file = True
            text = ""
            fm = {}
            if process:
                fm, text = parse_markdown_file(file)
                add_file = True if not keep_only_rooted else isinstance(fm, dict) and fm.get("rooted", False)
            
            if add_file:
                md_files[orig_file_name] = { 'file': slug, 'orig': orig, 'process': process, 'text': text, 'fm': fm }

    return md_files

def build_page_title(fm, file_name):
    """
    Check frontmatter, if name exists, use that, with title prepended if it exists.
    Otherwise, use the filename, changed to title case, with title prepended if it exists.
    """
    page_name = title_case(file_name.replace("-", " "), exclusions=EXCLUSIONS)
    page_title = ""

    if isinstance(fm, dict):    
        if fm.get("name"):
            page_name = title_case(fm.get("name"), exclusions=EXCLUSIONS)
        if fm.get("title"):
            page_title = title_case(fm.get("title"), exclusions=EXCLUSIONS)
    
    return " ".join([page_title, page_name]).strip()


################################
##### PARSE WEBSITE CONFIG #####
################################

configfile = "website.json"
with open((configfile), 'r', 2048, "utf-8") as f:
    data = json.load(f)
    source_dir = Path(data["source"])
    output_dir = Path(data["build"])
    target_date = data.get("export_date", None)
    target_campaign = data.get("campaign", None)
    slugify_files = data.get("slugify", True)
    clean_build_dir = data.get("clean_build", True)
    home_file = data.get("home_source", None)
    literate_nav = data.get("literate_nav", None)
    keep_only_rooted = data.get("keep_only_rooted", False)
    hide_tocs_tags = data.get("hide_toc_tags", [])
    exclude_tildes = data.get("exclude_tildes", True)

## SOURCE is input files
## OUTPUT is output directory

print("Source: " + str(source_dir))
print("Output: " + str(output_dir))

if clean_build_dir:
    print("Cleaning output directory " + str(output_dir) + " before building")
    shutil.rmtree(output_dir)

output_dir.mkdir(parents=True, exist_ok=True)

if home_file:
    print("Copying " + home_file + " to " + str(source_dir) + "/index.md")
    shutil.copy(Path(home_file), source_dir / "index.md")

source_files = build_md_list(source_dir, keep_only_rooted)
metadata = {}

print("Processing files")

for file_name in source_files:
    # Construct new path
    if slugify_files:
        new_file_path = output_dir / source_files[file_name]["file"]
    else:
        new_file_path = output_dir / source_files[file_name]["orig"]
    
    # Create directories if they don't exist
    new_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy files that won't be processed
    if not source_files[file_name]['process']:
        # just straight copy
        shutil.copy(source_dir / source_files[file_name]["orig"], new_file_path)
        continue

    # Open the input file
    fm = source_files[file_name]['fm']
    text = source_files[file_name]['text']

    # Get the mkdocs page path
    if slugify_files:
        page_path = source_files[file_name]['file']
    else:
        page_path = source_files[file_name]['orig']


    # clean up markdown text
    new_text = strip_date_content(text, target_date) if target_date else text
    new_text = strip_campaign_content(text, target_campaign) if target_campaign else new_text
    new_text = strip_comments(text) if data.get("strip_comments") else new_text
    new_text = re.sub(WIKILINK_RE, WikiLinkReplacer(output_dir, page_path, source_files, slugify_files), new_text) if data.get("fix_links") else new_text

    # clean up frontmatter
    page_title = build_page_title(fm, file_name)
    if isinstance(fm, dict):
        fm["title"] = page_title
    else:
        fm = { "title": page_title }

    # exclude toc from selected tags
    tags = fm.get("tags", [])
    if tags and hide_tocs_tags:
        clean_tags = list(set([piece for tag in tags for piece in tag.split("/")]))
        if any(tag in clean_tags for tag in hide_tocs_tags):
            fm["hide"] = ["toc"]

    new_frontmatter = yaml.dump(fm, sort_keys=False, default_flow_style=None, allow_unicode=True, Dumper=CustomDumper, width=2000)
    # write out new file
    output = "---\n" + new_frontmatter + "---\n" + new_text
    basename = Path(new_file_path).stem
    metadata[basename] = fm

    # Write the updated lines to a new file
    with open(new_file_path, 'w', 2048, "utf-8") as output_file:
        output_file.writelines(output)
 
## generate literate nav

if literate_nav:
    print("Generating nav file from template " + literate_nav)
    nav_generator = MkDocsNavigationGenerator(literate_nav, metadata, output_dir, exclude_tildes)
    processed_template = nav_generator.process_template()

    nav_path = output_dir / "toc.md"

    with open(nav_path, 'w') as output_file:
        output_file.write('\n'.join(processed_template))

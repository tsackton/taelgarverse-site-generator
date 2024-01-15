# How to Build the Taelgarverse Website

Taelgarverse is a website that is auto-generated from markdown files stored in an Obsidian vault. There are a number of steps that are required to convert dynamic Obsidian markdown notes into static markdown notes compatible with material for mkdocs, which is the static site generator used to create taelgarverse.

## Basic Workflow

We use a Obsidian-based Javascript code to prep a source directory for conversion, primarily to generate static, mkdocs-compliant versions of dynamic headers. We then use a Python script to auto-generate mkdocs-compliant markdown from the now-static source directory into the mkdocs `docs/` directory. 

Assuming the `source` directory is submodule, the basic build protocol for **local testing** is:
1. `git pull` from the source directory to get any updates to source material
2. (optional) run `python scripts/prep_source_dir.py` to remove files that you want to remove *prior* to export proccessing in Obsidian.
3. open the `source` directory as an Obsidian vault, and run the `prep_for_export` template to make dynamic pages static
4. run `python path/to/this/repo export_vault.py` to build the website, *from the website base directory that contains your mkdocs.yml*
5. run `mkdocs serve`

Note that things that live in the `docs` directory, including extra CSS and site images like banners and logos, are copied by the `export_vault.py` script. See config below. Things that live *outside* the `docs` directory (`overrides`) are not mananged by `export_vault.py`. 

## Configuration

The `export_vault.py` script has a number of configuration options, that can be set by changing the website.json file.

- "source": the source directory containing input files to be converted
- "build": the directory to put output in, which should be "docs" to work with mkdocs
- "home_source": the template for the home page
- "home_dest": the file to be created for the home page, in `"build"`, usually `index.md`
- "literate_nav_source": a template to generate the literate nav from
- "literate_nav_dest": the file to generate for the literate nav, must match mkdocs.yml
- "css_extras_source": source for extra css, copied unmodified to css_extras_dest
- "css_extras_dest": location in docs for css_extras, must match mkdocs.yml
- "site_images_source": directory of site images
- "site_images_dest": location in docs where site images are copied
- "campaign": a campaign key; if set, then text in between %%^Campaign:key%% %%^End%% blocks will be removed if key does not match the value in "campaign"
- "export_date": a date; if set, then text in bewteen %%^Date:date%% %%^End%% blocks will be removed if export_date < date
- "fix_links": logical; if true, will convert `[[wikilinks]]` to `[standard markdown](path/to/standard-markdown.md)` links
- "strip_comments": logical; if true, will remove text between %% %% blocks
- "slugify": logical, if true, will slugify file names and folder names when exporting to `build`
- "clean_build": logical, if true, will delete all files in `build` directory before starting processing
- "keep_only_rooted": logical, if true, will only process markdown files with rooted: True set in frontmatter
- "hide_toc_tags": list, if set will set hide: ["toc"] on pages that have a tag in the hide_toc_tags lists; overwrites `hide:` if set in the source directory
- "exclude_tildes": logical, if true will exclude unnamed (~Temp Name~) files from nav

The `export_vault.py` script does not manage theme overrides; these are generally not kept in the `docs` directory and so won't be deleted by `clean_build`. 

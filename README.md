# How to Build the Taelgarverse Website

Taelgarverse is a website that is auto-generated from markdown files stored in an Obsidian vault. There are a number of steps that are required to convert dynamic Obsidian markdown notes into static markdown notes compatible with material for mkdocs, which is the static site generator used to create taelgarverse.

## Basic Workflow

We use a Obsidian-based Javascript code to prep a source directory for conversion, primarily to generate static, mkdocs-compliant versions of dynamic headers. We then use a Python hook to auto-generate mkdocs-compliant markdown from the now-static source directory into the mkdocs `docs/` directory. 

Assuming the `source` directory is submodule, the basic build protocol for **local testing** is:
1. `git pull` from the source directory to get any updates to source material
2. (optional) run `python scripts/prep_source_dir.py` to remove files that you want to remove *prior* to export proccessing in Obsidian.
3. open the `source` directory as an Obsidian vault, and run the `prep_for_export` template to make dynamic pages static
4. run `mkdocs serve` to build the website

How this will be converted to github actions for serving the website is TBD but will involve some changes (since the staticification of the source has to be done offline via Obsidian).

## Configuration

The `export_vault.py` hook that is run by mkdocs has a number of configuration options, that can be set by changing the website.json file.

- "source": the source directory containing input files to be converted
- "build": the directory to put output in, which should be "docs" to work with mkdocs
- "campaign": a campaign key; if set, then text in between %%^Campaign:key%% %%^End%% blocks will be removed if key does not match the value in "campaign"
- "export_date": a date; if set, then text in bewteen %%^Date:date%% %%^End%% blocks will be removed if export_date < date
- "fix_links": logical; if true, will convert `[[wikilinks]]` to `[standard markdown](path/to/standard-markdown.md)` links
- "strip_comments": logical; if true, will remove text between %% %% blocks
- "slugify": logical, if true, will slugify file names and folder names when exporting to `build`
- "clean_build": logical, if true, will delete all files in `build` directory before starting processing
- "home_source": a file to be used as the home page; will be copied to `build/index.md`
- "keep_only_rooted": logical, if true, will only process markdown files with rooted: True set in frontmatter
- "hide_toc_tags": list, if set will set hide: ["toc"] on pages that have a tag in the hide_toc_tags lists; overwrites `hide:` if set in the source directory
- "literate_nav": a markdown file copied to docs as docs/toc.md to be used for the literate navigation plugin


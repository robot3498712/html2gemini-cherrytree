# html2gemini-cherrytree

This python3 program facilitates converting html to gmi files, with a focus on CherryTree exports.

## Usage

1. Install requirements.txt
2. Copy _config.py.template to _config.py
3. Edit config (and run script to create folder structure)
4. Place source html files in the input folder / export ctb

You will now find your .gmi files in the /of/gemini folder. You can run a server with those files and everything should work. This script is intended to be used on CherryTree html exports. Codeblocks are somewhat buggy from time to time.


## CherryTree Mod and General Notes

* Original projects (transformers such as now archived md2gemini) are somewhat inefficient.
> Upgrade to python 3.12 (full conversion done in 30s [py3.10] > 22s [py3.12] for my reference ctb).
> Enable incremental updates in config, using a hashtable (stored in script dir) for reference, to speed up consecutive runs.
> Open an issue if you can recommend better solutions.
* **Consider using a ram disk or tmpfs for file manipulation.**
> File ops cannot be avoided entirely.
* Index files use dot .prefix. You may want to change this.
> For agate see https://github.com/mbrubeck/agate/discussions/151


## Credits

Forked from https://github.com/akadius-one/Html2GeminiPy

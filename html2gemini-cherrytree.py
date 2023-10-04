#!/usr/bin/env python3
'''
html2gemini-cherrytree :: 0.1.0
author: robot 
'''

import sys, os, re, time, subprocess, bleach, hashlib, pickle, gzip
from chardet.universaldetector import UniversalDetector
from markdownify import markdownify
from types import SimpleNamespace
from md2gemini import md2gemini
from bs4 import BeautifulSoup
from pathlib import Path
from _config import cfg

def wipe(path): # might be faster to unlink dir, then recreate
	for root, dirs, files in os.walk(path):
		for file in files:
			os.remove(os.path.join(root, file))

def identCherryTree(path):
	html = open(str(path), "r", encoding="utf-8").read()
	soup = BeautifulSoup(html, 'html.parser')
	if soup.find('meta', content='CherryTree'):
		return (True, soup.find('title').string, soup) # like notes.ctb
	raise 'isNotCherryTree'

def get_paths(dir):
	pathList = []
	for itm in os.listdir(dir):
		path = os.path.join(dir, itm)
		pathList.append(path)
		try:
			pathList += get_paths(path)
		except:
			pass
	return pathList

def get_html(pathList):
	htmlList = []
	for path in pathList:
		if path.endswith(".html") or path.endswith(".htm"):
			htmlList.append(path)
	return htmlList

tags = [
	'a',
	'p',
	'abbr',
	'acronym',
	'b',
	'blockquote',
	'big',
	'br',
	'code',
	'em',
	'i',
	'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7',
	'hr',
	'li',
	'ol',
	'pre',
	'style',
	'ul'
]

attr = {
	'a': ['href', 'title', 'name', 'alt'],
	'abbr': ['title'],
	'acronym': ['title'],
	'style': ['type']
}

def convert_html_to_stripped_html(g):
	remove_head(g)
	g.txt = bleach.clean(
		g.txt,
		tags=tags,
		attributes=attr,
		strip=True,
		strip_comments=True
	)
	g.txt = g.txt.replace("<br/>", "\n").replace("<br>", "\n")
	g.txt = g.txt.replace("<hr/>", "-"*30).replace("<hr>", "-"*30)
	remove_heading_newlines(g)
	g.txt = g.txt.strip()

def remove_head(g):
	start = re.search("<head>", g.txt, re.IGNORECASE)
	end = re.search("</head>", g.txt, re.IGNORECASE)

	if start:
		start = start.span()[0]
	if end:
		end = end.span()[1]
		if not start:
			start = 0

		g.txt = g.txt[:start] + g.txt[end:]

def remove_heading_newlines(g): # what is this doing?
	for h_num in range(1, 7):
		pos = 0
		last = 0
		html_sep = []

		h = "h" + str(h_num)
		h_open = re.compile(re.escape(f"<{h}>"))
		h_close = re.compile(re.escape(f"</{h}>"))

		start = h_open.search(g.txt, pos)

		while start is not None :
			start = start.span()[1]
			pos = start
			end = h_close.search(g.txt, pos)

			if end is not None :
				pos = end.span()[1]
				end = end.span()[0]

				heading = g.txt[start:end]
				heading = heading.replace("\r", "")
				heading = heading.replace("\n", "")

				html_sep.append(g.txt[last:start])
				html_sep.append(heading)
				html_sep.append(g.txt[end:pos])

			last = pos
			start = h_open.search(g.txt, pos)

		html_sep.append(g.txt[last:])
		g.txt = "".join(html_sep)
# end remove_heading_newlines()

def convert_html_to_md(g):
	g.txt = markdownify(g.txt, strip=['style'], heading_style="ATX")
	# blockquote indented
	lines = g.txt.split("\n")
	for ln, line in enumerate(lines):
		if line.startswith(" "):
			lines[ln] = f">{line}"
	g.txt = "\n".join(lines)

def convert_md_to_gemini(g):
	# https://github.com/makew0rld/md2gemini
	# copy|default|..
	g.txt = md2gemini(g.txt, links="default")
	g.txt = re.sub(r'[\r\n][\r\n]{2,}', '\n\n', g.txt)
	g.txt = g.txt.replace("&amp;", "%26") # appears being a bug
	links_to_gemini(g)

def links_to_gemini(g):
	lines = g.txt.split("\n")

	for ln, line in enumerate(lines):
		if ".html" in line and "http" not in line or cfg.domain in line:
			line = line.replace("html", "gmi")
			try:
				url = line.split(" ")[1]
				link = url.split("/")[-1]
			except:
				pass
			else:
				lines[ln] = line.replace(str(url), str(link))
	g.txt = "\n".join(lines)

def convert_to_utf8(g): # dubious
	g.detector.reset()
	with open(g.pathInput, 'rb') as f:
		b = f.read()
		f.seek(0, 0)
		for line in f:
			g.detector.feed(line)
			if g.detector.done:
				break
		g.detector.close()

	encoding = g.detector.result["encoding"]
	if encoding in ['utf-8', 'ascii']: g.txt = b.decode('utf-8')
	else: g.txt = b.decode(encoding)

def file_exists(file_path):
	if not os.path.exists(file_path):
		return False
	if os.path.getsize(file_path) == 0:
		return False
	return True

def run(jobs):
	for run in jobs:
		if not run['a']: continue
		try: assert eval(run['e'])
		except AssertionError: pass
		else:
			if '^' in run: print(run['^'])
			subprocess.Popen(run['c'], shell=True, stdout=subprocess.PIPE).stdout.read()
			if '$' in run: print(run['$'])

def convert(outputPath, htmlList):
	startTime = time.time()
	ns = SimpleNamespace()

	for ns.pathInput in htmlList:
		if not ns.pathInput.endswith(".html") and not ns.pathInput.endswith(".htm"):
			continue

		if not isCherryTree:
			ns.detector = UniversalDetector()
			convert_to_utf8(ns)
		else: # no need to bother with the wonky detection
			with open(ns.pathInput, 'rb') as f:
				b = f.read()
			ns.txt = b.decode('utf-8')

		convert_html_to_stripped_html(ns)
		convert_html_to_md(ns)
		convert_md_to_gemini(ns)

		fileOutput = os.path.join(outputPath, "./gemini/", f"{Path(ns.pathInput).stem}.gmi")
		if cfg.overwrite or not file_exists(fileOutput):
			with open(fileOutput, "w", encoding="utf-8") as f:
				f.write(ns.txt)
	# end FOR
	print("conversion completed in %d seconds" % (int(time.time() - startTime),))
# end convert()

if __name__ == "__main__":
	sd, isCherryTree, cherryTreeDb = os.path.dirname(os.path.realpath(__file__)), False, None

	# pre-processing
	run(cfg.run["pre"])

	# setup and cleanup
	inputPath = os.path.join(cfg.workingDir, cfg.inDir)
	outputPath = os.path.join(cfg.workingDir, cfg.outDir)

	for d in ["./gemini/", "./tmp/"]:
		try: os.makedirs(os.path.join(outputPath, d))
		except: pass

	if not os.path.isdir(inputPath):
		os.makedirs(inputPath)
		sys.exit(0)

	if cfg.wipe: wipe(outputPath)

	htmlList = get_html(sorted(get_paths(inputPath)))
	if not len(htmlList): sys.exit(0)

	# cherrytree (multiple file) html export essentially is a double-dash-delimited flat filesystem
	try:
		(isCherryTree, cherryTreeDb, soup) = identCherryTree(os.path.join(inputPath, "index.html"))
	except: pass

	# processing
	if (isCherryTree): # first create (html) .index files to facilitate navigation
		# creating gmi files may be better; see convert_md_to_gemini() and link modes
		def Tree(ul, root=None):
			result = {}
			for el in ul.findChildren(['li'], recursive=False):
				a = el.find('a')
				key = a['onclick'].replace("changeFrame('", '')[:-2]
				# ul.subtree always follows li
				_next = el.find_next_sibling()
				_next and (_class := _next.get('class')) or (_class := [])
				# recurse if adjacent ul.subtree
				result[key] = {
					'txt': a.text,
					'root': root,
					'subtree': Tree(_next, Path(key).stem) if ('subtree' in _class) else None
				}
			# end FOR
			return result
		# end Tree()

		def WalkTree(obj, level=-1):
			level +=1
			subtrees, itms = [], []
			for key in obj:
				if obj[key]['subtree'] is not None:
					subtrees.append(obj[key]['subtree'])
					itms.append(f"<a href=\".{key}\">{obj[key]['txt']}/*</a>")

				itms.append(f"<a href=\"{key}\">{obj[key]['txt']}</a>")
			# end FOR
			of = os.path.join(outputPath, "./tmp/",
				"index.html" if not level else f".{obj[key]['root']}.html")
			with open(of, 'w', encoding='utf-8') as f:
				f.write("".join(itms)) # for fancy delimiters edit above

			htmlList.append(of)

			for subtree in subtrees:
				WalkTree(subtree, level)
		# end WalkTree()

		result = Tree(soup.find('ul', class_='outermost'))
		WalkTree(result)
		htmlList.remove(os.path.join(inputPath, "index.html"))

		if cfg.incremental:
			hdbfp, htmlListDelta = os.path.join(sd, f"{cherryTreeDb}.bin"), []
			try:
				with gzip.open(hdbfp, "rb") as f:
					hdb = pickle.load(f)
			except: hdb = {}

			for fp in htmlList:
				h = hashlib.sha256()
				with open(fp, 'rb') as f:
					while True:
						chunk = f.read(h.block_size)
						if not chunk: break
						h.update(chunk)
				digest = h.digest()

				if (not fp in hdb) or (hdb[fp] != digest):
					hdb[fp] = digest
					htmlListDelta.append(fp)
			# end FOR
			if len(htmlListDelta):
				with gzip.open(hdbfp, 'wb') as f:
					pickle.dump(hdb, f, pickle.HIGHEST_PROTOCOL)

			htmlList = htmlListDelta
		# end IF incremental
	# end IF isCherryTree
	print("indexing completed")

	if len(htmlList):
		convert(outputPath, htmlList)
	else:
		print("empty payload")

	# post-processing
	run(cfg.run["post"])

	sys.exit(0)
# end __main__

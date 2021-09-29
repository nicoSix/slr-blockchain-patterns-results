import json
import re
from string import Template

capital_word_list = [
  "BPM"
]

def capitalizeURI(word):
  if word not in capital_word_list:
     return word.capitalize()
  else:
    return word

def getPaperPatternFromId(papers, paper_id):
  for p in papers:
    if p['ID'] == paper_id:
      return p
  return False

def isNameInCanonicals(name, canonical_patterns):
  for c in canonical_patterns:
    if parseToURI(name) == parseToURI(c['Name']):
      return True
  return False
  
def getFirstAuthor(authors):
  return re.split(', ', authors)[0]

def parseToURI(name):
  nameArray = re.split('[, \-!?:()/&*]+', name)
  nameArray = [capitalizeURI(word) for word in nameArray]
  name = ''.join(nameArray)
  return name

def parseToRelation(name):
  nameArray = re.split('[, \-!?:()/&*]+', name)
  nameArray = [nameArray[0].lower()] + [capitalizeURI(nameArray[i]) for i in range(1, len(nameArray)) if i != 0]
  name = ''.join(nameArray)
  return name

def get_links_between_patterns(paper_patterns, paper_pattern, paper, canonical_patterns):
  link_types = ["From pattern", "Related to", "Variant Of", "Requires", "Benefits from"]
  relation_template = loadTemplate('relation')
  relations_str = ''

  for key in link_types:
    if key in paper_pattern:
      relations = re.split(', ', paper_pattern[key])
      for r in relations:
        if r.isdigit():
          relation_paper = getPaperPatternFromId(paper_patterns, r)
          relation_paper_name = parseToURI(relation_paper['Name']) + getFirstAuthor(paper['author']) + paper['year']
        else:
          if isNameInCanonicals(r, canonical_patterns):
            relation_paper_name = parseToURI(r) + "Canonical"
          else:
            relation_paper_name = "Unknown"
        relations_str += Template(relation_template).substitute(relation=parseToRelation(key), value=relation_paper_name)

  return relations_str

def loadSLRData():
  with open('patterns_data.json', 'r') as file:
    data = json.load(file)
    return data['Papers'], data['Paper patterns'], data['Canonical patterns']

def loadTemplate(item):
  with open('./templates/' + item + '.txt', 'r') as file:
    return file.read()

def createExempleToCanonicalMappings(canonical_patterns):
  example_mapping = {}

  for c in canonical_patterns:
    if 'Alternative names' in c:
      for an in c['Alternative names'].split(', '):
        example_mapping[parseToURI(an)] = parseToURI(c['Name'])
    example_mapping[parseToURI(c['Name'])] = parseToURI(c['Name'])

  return example_mapping

def parseToOntologyLiteralIfExists(item, key):
  if key in item:
    return item[key].replace('"', '')
  else:
    return ""

def run():
  papers, paper_patterns, canonical_patterns = loadSLRData()
  classes = ''
  canonicals = ''
  examples = ''
  class_template = loadTemplate('class')
  canonical_template = loadTemplate('canonical')
  example_template = loadTemplate('paper')
  example_mapping = createExempleToCanonicalMappings(canonical_patterns)

  for p in canonical_patterns:
    patternType = parseToURI(p['Type (determined)'])
    if patternType == "ArchitecturalPattern" or patternType == "Idiom":
      patternCategory = patternType
    else:
      if "Subsubcategory" in p:
        patternCategory = parseToURI(p['Subsubcategory'])
      else:
        patternCategory = parseToURI(p['Subcategory'])

    classes += Template(class_template).substitute(
      owner="nicolas", 
      uri=parseToURI(p['Name']), 
      name=p['Name'], 
      category=patternCategory
    )

    canonicals += Template(canonical_template).substitute(
      owner="nicolas", 
      uri=parseToURI(p['Name']), 
      name=p['Name'], 
      technology=parseToURI(p['Target (generalized)']), 
      domain=parseToURI(p['Applicability domain (generalized)']), 
      refClass=parseToURI(p['Name']), 
      examples='', 
      context='', 
      solution=''
    )

  for p in paper_patterns:
    paper = getPaperPatternFromId(papers, p['Paper'])
    patternType = parseToURI(p['Type (determined)'])
    if patternType == "ArchitecturalPattern" or patternType == "Idiom":
      patternCategory = patternType
    else:
      if "Subsubcategory" in p:
        patternCategory = parseToURI(p['Subsubcategory'])
      else:
        patternCategory = parseToURI(p['Subcategory'])

    examples += Template(example_template).substitute(
      owner="nicolas", 
      uri=parseToURI(p['Name']), 
      name=p['Name'], 
      technology=parseToURI(p['Target']), 
      domain=parseToURI(p['Applicability domain']), 
      refClass=example_mapping[parseToURI(p['Name'])], 
      context=parseToOntologyLiteralIfExists(p, 'Context & Problem'), 
      solution=parseToOntologyLiteralIfExists(p, 'Solution'),
      author=getFirstAuthor(paper['author']),
      year=paper['year'],
      links=get_links_between_patterns(paper_patterns, p, paper, canonical_patterns)
    )
  
  with open("./results/classes.ttl", "w") as text_file_classes:
    text_file_classes.write(classes)

  with open("./results/canonicals.ttl", "w") as text_file_canonicals:
    text_file_canonicals.write(canonicals)

  with open("./results/examples.ttl", "w") as text_file_examples:
    text_file_examples.write(examples)

run()
#import argparse
import xml.etree.ElementTree as ET
from datetime import date
from owlready2 import *
#import types
import warnings
#import pdb # pdb.set_trace()


# -----------------------------------------
# argparse
# -----------------------------------------

# python phsToOntology.py -i data/colao_merged.owl -p data/phs_colao_AP.xml -o out.owl
# parser = argparse.ArgumentParser(description='Convert Phenoscript XML into OWL',
#                                  usage='python phsToOntology.py -i in.owl -p in.xml -o out.owl'
#                                  )
# parser.add_argument("-i",  "--inonto", help="input ontology", required=True)
# parser.add_argument("-p", "--phs",  help="input PhenoScript XML")
# parser.add_argument("-o", "--output", help="output ontology")
# args = parser.parse_args()

# print(args.inonto)
# print(args.phs)
# print(args.output)
# -----------------------------------------

# -----------------------------------------
# Arguments
# -----------------------------------------
# phsXML= args.phs
# ontoPath= args.inonto.rsplit('/', 1)[0]
# ontoFile= args.inonto.rsplit('/', 1)[-1]
# outputFile=args.output
# # phsXML="/Users/taravser/Documents/My_papers/Semantic_discriptions/Protege/PhenoScript_R/test/COLAO/results/phs_colao_AP.xml"
# # ontoPath="/Users/taravser/Documents/My_papers/Semantic_discriptions/Protege/PhenoScript_R/test/COLAO/data/ontologies"
# # ontoFile="colao_merged.owl"
# -----------------------------------------


#onto_out = get_ontology("http://tmpsmpmpm#")

# additional (default) Args
phs='{https://github.com/sergeitarasov/PhenoScript}'
ns = {'phs': 'https://github.com/sergeitarasov/PhenoScript'}
phsVersion="1.0.0"

print('Reading data...\n')

#--- Read in PhS xml
tree = ET.parse(phsXML)
root = tree.getroot()

#--- Read in Ontology
set_log_level(9)
onto_path.append(ontoPath)
onto = get_ontology(ontoFile)
onto.load(reload_if_newer=True)
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
inf=onto.get_namespace("https://github.com/sergeitarasov/PhenoScript/inference/")
tdwg = onto.get_namespace('http://rs.tdwg.org/dwc/terms/')
#xxx=onto.get_namespace("29-07-2022-16-18-35/")

#-----------------------
# Functions
#-----------------------

# given a list of xml nodes, select unique ones based on attribute attr
def xmlUniqueNodes(nodesXML, attr):
    # attr=phs + 'node_id'
    childID = []
    unique_childrenXML = []
    for child in nodesXML:
        i = child.get(attr)
        if i not in childID:
            childID.append(i)
            unique_childrenXML.append(child)
    return unique_childrenXML

# convert PhenoScript numeric node to porper numbers
def phsNumbersToOWL(str_value, type):
    if(type=='real'):
        out=float(str_value)
    elif(type=='int'):
        out=int(str_value)
    else:
        warnings.warn('Unknown numeric type, see: phsNumbersToOWL()')
    return out

#-----------------------
# Create Annotations
#-----------------------

with inf:
    class Penoscript_annotations(AnnotationProperty): pass
    class PhenoScript_original_class(Penoscript_annotations): pass
    class PhenoScript_implies_absence_of(Penoscript_annotations): pass
    class PhenoScript_NL(Penoscript_annotations): pass
    class PhenoScript_original_assertion(Penoscript_annotations): pass

with tdwg:
    class catalogNumber(AnnotationProperty): pass

# Annotationds for triples
# inf.PhenoScript_original_assertion[focal_sp, obo.IAO_0000219, focal_org ] = True
# inf.PhenoScript_original_class[focal_sp, obo.IAO_0000219, focal_org ]

#-----------------------
# Make nodes
#-----------------------

# get unique nodes
print('Creating nodes...\n')

nodeID=[]
# get unique nodes except those that have phs:fromNegativeEdge='True'
for node in root.iter(phs+'node'):
    # root.findall(".//phs:node", ns)
    # root.findall(".//phs:node[@phs:fromNegativeEdge='False']", ns)
    is_negEdge = eval(node.get(phs + 'fromNegativeEdge'))
    if is_negEdge==False:
        nodeID.append(node.get(phs + 'node_id'))


# get unique
nodeIDunique=list(set(nodeID))


# create new nodes
# ni = nodeIDunique[1]
#destroy_entity(newNode)
#onto.destroy()
for ni in nodeIDunique:
    node = root.find(".//phs:node[@phs:node_id='%s']" % ni, ns)
    #print(node)
    nodeClass = node.get(phs + 'iri')
    # this piece of code uses a workaround for iri cuz Owlready does not assign it correctly
    # when using the direct approach newNode = IRIS[nodeClass](ni)
    # create new node
    #newNode = IRIS[nodeClass]('https://temp/tmp')
    nodeClassObj=IRIS[nodeClass]
    newNode = nodeClassObj('https://temp/tmp')
    newNode.iri=ni
    #print(newNode.iri)

    # getting labels
    label = node.find(".//phs:node_property[.='rdfs:label']", ns)
    if (label is not None):
        #print(label.text, label.get(phs + 'value'))
        newNode.label = label.get(phs + 'value')
    elif (label is None):
        className=IRIS[nodeClass].label
        newNode.label = className[0]+':'+ ni.rsplit('/', 1)[-1]

    # getting catalog number
    catalogNumber_value = node.find(".//phs:node_property[.='catalogNumber']", ns)
    if (catalogNumber_value is not None):
        newNode.catalogNumber = catalogNumber_value.get(phs + 'value')

    # add annotations
    newNode.created_by = "PhenoScript v. " + phsVersion
    # add date
    today = date.today()
    dt_string = today.strftime("%d/%m/%Y")
    newNode.creation_date = dt_string
    # add original class annotation
    newNode.PhenoScript_original_class.append(nodeClassObj)




#-----------------------
# Make edges between nodes
##  ............................................................................
##  Compile N E N: phs:node pos=1 -> E pos=2 -> (phs:node | phs:nested_node | phs:list_node)  pos=3    ####
#-----------------------

print('Adding edges between nodes...\n')

# make mapping to extract parents quickly
parent_map = {c:p for p in root.iter() for c in p}
#parent_map[nodePos1[0]]

# select node triple_pos=1
nodePos1=root.findall(".//phs:node[@phs:triple_pos='1']", ns)
#len(nodePos1)


#----------------------
# nodeXML = nodePos1[20]
for nodeXML in nodePos1:
    parentXML=parent_map[nodeXML]
    edgeXML=parentXML.findall("./*[@phs:triple_pos='2']", ns)
    Pos3XML=parentXML.findall("./*[@phs:triple_pos='3']", ns)
    is_negEdge = eval(edgeXML[0].get(phs + 'negative_prop'))
    #
    if (is_negEdge==False):
        #
        #continue
        #print(is_negEdge)
        #
        if (Pos3XML[0].tag == phs + 'node'):
            # print('ok')
            N1 = IRIS[nodeXML.get(phs + 'node_id')]
            N2 = IRIS[Pos3XML[0].get(phs + 'node_id')]
            Ed = IRIS[edgeXML[0].get(phs + 'iri')]
            if owl.FunctionalProperty in Ed.is_a:
                exec('N1.%s = N2' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            else:
                exec('N1.%s.append(N2)' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            #
        elif (Pos3XML[0].tag == phs + 'list_node'):
            # print('list_node')
            #
            N1 = IRIS[nodeXML.get(phs + 'node_id')]
            Ed = IRIS[edgeXML[0].get(phs + 'iri')]
            childrenXML = Pos3XML[0].findall(".//phs:node[@phs:triple_pos='NO']", ns)

            for child in childrenXML:
                N2 = IRIS[child.get(phs + 'node_id')]
                if owl.FunctionalProperty in Ed.is_a:
                    exec('N1.%s = N2' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
                else:
                    exec('N1.%s.append(N2)' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            #
        elif (Pos3XML[0].tag == phs + 'nested_node'):
            # print('nested_node')
            #
            N1 = IRIS[nodeXML.get(phs + 'node_id')]
            Ed = IRIS[edgeXML[0].get(phs + 'iri')]
            childrenXML = Pos3XML[0].findall(".//phs:node", ns)
            #
            # get unique nodes based on their ids
            unique_childrenXML = xmlUniqueNodes(childrenXML, attr=phs + 'node_id')
            for child in unique_childrenXML:
                # print('child: ', child.attrib)
                N2 = IRIS[child.get(phs + 'node_id')]
                if owl.FunctionalProperty in Ed.is_a:
                    exec('N1.%s = N2' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
                else:
                    exec('N1.%s.append(N2)' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            #
        elif (Pos3XML[0].tag == phs + 'numeric_node'):
            # print(Pos3XML[0].attrib)
            N1 = IRIS[nodeXML.get(phs + 'node_id')]
            Ed = IRIS[edgeXML[0].get(phs + 'iri')]
            N2_type = Pos3XML[0].get(phs + 'numeric_type')
            N2_value = Pos3XML[0].get(phs + 'node_name')
            N2 = phsNumbersToOWL(N2_value, N2_type)
            # [owl.DatatypeProperty, owl.FunctionalProperty] obo.IAO_0000004.is_a
            if owl.FunctionalProperty in Ed.is_a:
                exec('N1.%s = N2' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            else:
                exec('N1.%s.append(N2)' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            #
        else:
            #print('WARNING: something is wrong in "for nodeXML in nodePos1: ... else:"')
            warnings.warn('something is wrong  with Pos3XML[0].tag in "for nodeXML in nodePos1: ... else:"')
            #
    elif (is_negEdge == True):
        if (Pos3XML[0].tag == phs + 'node'):
            # print(is_negEdge)
            #
            N1 = IRIS[nodeXML.get(phs + 'node_id')]
            # N2 = IRIS[Pos3XML[0].get(phs + 'node_id')]
            classN2 = IRIS[Pos3XML[0].get(phs + 'iri')]
            Ed = IRIS[edgeXML[0].get(phs + 'iri')]
            #
            # --------------------------------
            # obo.BFO_0000051  # has_part
            # --------------------------------
            #exec('N1.is_a.append( obo.BFO_0000051.some( Not(%s.some(classN2) ) ) )' % Ed)
            exec('N1.is_a.append( Not(%s.some(classN2)  ) )' % Ed)
            # add annotation for absence
            N1.PhenoScript_implies_absence_of.append(classN2)

            # N2.is_a.append(obo.HAO_0001017) # this works
            # N2.is_a.append(obo.BFO_0000051.some(obo.HAO_0001017)) # this works
            # N2.is_a.append(obo.BFO_0000051.some( Not(obo.BFO_0000051.some(obo.HAO_0001017)) ))  # this works
        else:
            warnings.warn('Something is wrong with Pos3XML[0].tag in "for nodeXML in nodePos1: ... elif (is_negEdge == True): ...."')





##  ............................................................................
##  Compile N E N: (phs:nested_node | phs:list_node) pos=1 -> E pos=2 -> (phs:node) pos=3    ####

print('Adding edges between nested and list nodes...\n')

# select list or nested nodes, triple_pos=1
nodePos1=root.findall(".//phs:nested_node[@phs:triple_pos='1']", ns) + root.findall(".//phs:list_node[@phs:triple_pos='1']", ns)

# nodeXML = nodePos1[0]
for nodeXML in nodePos1:
    parentXML=parent_map[nodeXML]
    edgeXML=parentXML.findall("./*[@phs:triple_pos='2']", ns)
    Pos3XML=parentXML.findall("./phs:node[@phs:triple_pos='3']", ns)
    is_negEdge = eval(edgeXML[0].get(phs + 'negative_prop'))
    #
    if (Pos3XML[0].tag == phs + 'node' and is_negEdge==False):
        N1_childrenXML = nodeXML.findall(".//phs:node", ns)
        N1_unique_childrenXML = xmlUniqueNodes(N1_childrenXML, attr=phs + 'node_id')
        Ed = IRIS[edgeXML[0].get(phs + 'iri')]
        N2=IRIS[Pos3XML[0].get(phs + 'node_id')]
        # child=N1_unique_childrenXML[0]
        for child in N1_unique_childrenXML:
            N1 = IRIS[child.get(phs + 'node_id')]
            if owl.FunctionalProperty in Ed.is_a:
                exec('N1.%s = N2' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
            else:
                exec('N1.%s.append(N2)' % Ed.name)
                inf.PhenoScript_original_assertion[N1, Ed, N2] = True
    else:
        warnings.warn('something is wrong  with "Pos3XML[0].tag == phs + node and is_negEdge==False" when phs:triple_pos=1 is not a simple node')



##  ............................................................................
##  Linking OTU and OPHUs    ####

print('Linking OTU model with OPHUs...\n')
OTUs=root.findall(".//phs:otu_object", ns)

# loop over otu_objects (i.e. species). in each otu_obj identify nodes that link all ophus
# otu = OTUs[0]
for otu in OTUs:
    # get all phs:node_property
    props=otu.findall(".//phs:otu_properties//phs:node_property", ns)
    # get all nodes in phs:ophu_list for the otu that are fromNegativeEdge='False'
    ophuList = otu.findall(".//phs:ophu_list", ns)
    ophuNodes = ophuList[0].findall(".//phs:node[@phs:fromNegativeEdge='False']", ns)
    for p in props:
        if p.text=='to_Ophu_List':
            parentXML = parent_map[p]
            N1=IRIS[parentXML.get(phs+'node_id')]
            Ed=IRIS[p.get(phs+'iri')]
            #print(p.text, p.get(phs+'value'), p.get(phs+'iri'), parentXML.get(phs+'node_id'))
            #print(N1, Ed)
            for node in ophuNodes:
                N2=IRIS[node.get(phs+'node_id')]
                if owl.FunctionalProperty in Ed.is_a:
                    exec('N1.%s = N2' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
                else:
                    exec('N1.%s.append(N2)' % Ed.name)
                    inf.PhenoScript_original_assertion[N1, Ed, N2] = True
#
#


# # Adding necessary classes for Reasoning
# inf=onto.get_namespace("https://github.com/sergeitarasov/PhenoScript/inference/")
#
# # New class
# with inf:
#     class phsEncirclesSome(Thing): pass
#     phsEncirclesSome.equivalent_to.append(obo.AISM_0000078.some(Thing))
#         # AISM_0000078 encircles


#--- Save

onto.save(file = outputFile, format = "rdfxml")

print('\n DONE!!!\n')

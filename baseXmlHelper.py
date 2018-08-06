# Copyright: 2018, Ableton AG, Berlin. All rights reserved.

#****************************************************************************************
#
# base xml parse functionality
#
#****************************************************************************************


try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET

import fnmatch, re, os
from cStringIO import StringIO
import gzip
import hashlib

#----------------------------------------------------------------------------------------

class xml_helper:
  def __init__(self, filepath=None, tree=None):

    self.tree = tree

    self.mFilePath = filepath

    self.ParentMap = None

    self.mReplaceNewline = True

  #----------------------------------------------------------------------------------------
  def load_xml(self, filepath=None, escapeNewline=True, maxSize=0, createMap=True):
    """
    load xml from filepath
    """

    if filepath != None:
      self.mFilePath = filepath
    self.mReplaceNewline = escapeNewline

    if not os.path.exists(str(self.mFilePath)):
      print "Warning: The filepath '%s' does not exist. Please make sure to pass the right path as load_xml('foo/bar')" %filepath
      return False

    if not escapeNewline:
      try:
        input = StringIO(gzip.open(self.mFilePath, "r").read())
      except IOError:
        input = StringIO(open(self.mFilePath, "r").read())


    else:
  # replace Live's newline string with a dummy ###newline_escape###
  # we will revert this back on writing.
  # using the escapeNewline is slow on large documents

      try:
        file = gzip.open(self.mFilePath, "r").read()
      except IOError:
        file = open(self.mFilePath, "r").read()

      input = StringIO(re.sub(r"&#x0[DA];", "###newline_escape###", file))

      del(file)   # save memory

    if maxSize:
      maxSize = maxSize*1048576 # in MB
      if len(input.getvalue()) > maxSize:
        print "Warning: Large Document - skipping %s" %filepath
        return False

    self.tree = ET.ElementTree(file=input)

    input.close()

    if createMap:
      self.child_to_parent_dict()

    return True


  def getroot(self):
      return self.tree.getroot()


  #----------------------------------------------------------------------------------------
  def new_xml(self, root_name):
    """
    create a new (empty) xml tree
    """

    self.tree = ET.ElementTree(ET.fromstring('<?xml version="1.0" encoding="UTF-8"?><%s></%s>'%(
                                                                            root_name, root_name)))
    return self.tree.getroot()

  #----------------------------------------------------------------------------------------
  def return_tree(self):
    """
    return tree and dict with ParentMap
    """

    return self.tree, self.ParentMap

  #----------------------------------------------------------------------------------------
  def fn_to_reg(self, searchItems):
    """ return a list of RegEx from searchItems"""
    return [re.compile(fnmatch.translate(s)) for s in searchItems]


  #----------------------------------------------------------------------------------------
  def find_nodes(self, searchItems, root=None, sortByDepth=False):

    if root == False:
      print "Hey, you are passing 'False' as the root to find_nodes. Fix your script."

    ListOfSearchItems = list(searchItems)

    if root == None:
      Parent = ListOfSearchItems.pop(0)
      Out = [x for x in self.ParentMap.keys() if x.tag == Parent]

    else:
      Out = [root]

    while len(ListOfSearchItems) > 0:
      Parent = ListOfSearchItems.pop(0)
      Out = [x for root in Out for x in root.getiterator(Parent)]

    if sortByDepth == False: return Out

    TDict = dict((x, len(self.get_path_to_node(x))) for x in Out)
    return [o[0] for o in sorted(TDict.items(),key=lambda x:x[1])]


  #----------------------------------------------------------------------------------------
  def find_node(self, searchItems, root=None):

    try:
      return self.find_nodes(searchItems, root, sortByDepth=True)[0]
    except IndexError:
      return False


  #----------------------------------------------------------------------------------------
  def _refind_nodes(self, reSearchItems, root=None, sortByDepth=False):
    """
    Recursive Search for nodes. Same as find_allnodes, except input is a regex
    """

    reListOfSearchItems = list(reSearchItems)

    if root == None:
      ReParent = reListOfSearchItems.pop(0)
      Out = [x for x in self.ParentMap.keys() if ReParent.match(x.tag)]

    else:
      Out = [root]


    while len(reListOfSearchItems) > 0:
      ReParent = reListOfSearchItems.pop(0)
      Out = [x for root in Out for x in root.iter() if ReParent.match(x.tag)]

    if sortByDepth == False: return Out

    TDict = dict((x, len(self.get_path_to_node(x))) for x in Out)
    return [o[0] for o in sorted(TDict.items(),key=lambda x:x[1])]


  #----------------------------------------------------------------------------------------
  def child_to_parent_dict(self,):
    """create a dict to map child to parent for each node.
    """

    self.ParentMap = dict((c, p) for p in self.tree.iter() for c in p)
    self.ParentMap[self.tree.getroot()] = None
    return self.ParentMap


  #----------------------------------------------------------------------------------------
  def get_parent_node(self, node):

# much more efficient:
    try: return self.ParentMap[node]
    except (KeyError, IndexError, TypeError): self.child_to_parent_dict()

    return self.ParentMap[node]

  #----------------------------------------------------------------------------------------
  def get_path_to_node(self, node):

    Path = []


    Parent = self.get_parent_node(node)

    while Parent != None:
      Path.insert(0, Parent)
      Parent = self.get_parent_node(Parent)

    return Path

  #----------------------------------------------------------------------------------------
  def set_nodevalue(self, node, value, V="Value", Conditional=False):
    """
    update the value of an xml node
    if Conditional, then check value first and return None if
    the old value is already the same as the new value
    """

    if self.mReplaceNewline:
      value = re.sub("\n", "###newline_escape###",value)

    if Conditional:
      if self.get_nodevalue(node, V) == value: return None

    node.set(V, value)
    return node

  #----------------------------------------------------------------------------------------

  def add_node(self, parent_node, new_node_name, attributes={}, position=0):
    """
    add a new xml node below parent_node
    attributes is a dict {"Value":"0.0"}
    """
    for key in attributes:
      attributes[key] = format(attributes[key])

    if position == -1:
      count_children = len(list(parent_node))
      position = count_children

    new_node = ET.Element(new_node_name, attributes)
    parent_node.insert(position, new_node)

    return new_node

  #----------------------------------------------------------------------------------------
  def get_nodevalue(self, node, V="Value"):
    """
    get node value
    """

    if node == False:
      return node

    return node.get(V)

  #----------------------------------------------------------------------------------------
  def get_parametervalue(self, nodename=None, node=None, root=None):
    """
    return FloatEvent, BoolEvent or EnumEvent of a parameter node
    """

    if nodename != None:
      node = self.find_node(nodename, root)

    node_event = self._refind_nodes(self.fn_to_reg(["Manual"]), root=node)[0]

    node_event_value = self.get_nodevalue(node_event)

    return node_event_value


  #----------------------------------------------------------------------------------------
  def set_parametervalue(self, Value, nodename=None, node=None, root=None, ):
    """
    return FloatEvent, BoolEvent or EnumEvent of a parameter node
    """

    if nodename != None:
      node = self.find_node(nodename, root)

    node_event = self._refind_nodes(self.fn_to_reg(["Manual"]), root=node)[0]

    if node_event != False:
      self.set_nodevalue(node_event, Value)
      return True

    return False


  #----------------------------------------------------------------------------------------
  def indent(self, elem, level=0):
    """proper indent out, copied from http://effbot.org/zone/element-lib.htm"""

    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            self.indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i



  #----------------------------------------------------------------------------------------
  def write_xml(self, filepath=None, escapeNewline=True, indent=False):
    """
    write new xml out
    if escapeNewline then we write to a string buffer and replace
    ###newline_escape### to &#x0A; to enforce correct line breaks """

    if not filepath:
      filepath = self.mFilePath

    if indent:
      self.indent(self.tree.getroot())

    output = StringIO()

    self.tree.write(output, encoding="UTF-8")

    outFile = open(filepath, "w")
    if escapeNewline:
      # we need to make sure newline &#x0A; is written correctly
      print >> outFile, re.sub("###newline_escape###", "&#x0A;", output.getvalue())
    else:
      print >> outFile, output.getvalue()

    outFile.close


#========================================================================================
# end of file
#========================================================================================

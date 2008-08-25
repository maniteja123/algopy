#!/usr/bin/env python

global_VariableVertexNumber = 0
global_FunctionVertexNumber = 0
global_VertexNumber = 0
global_EdgeNumber = 0

class Vertex:
	def __init__(self, vertex_type):
		global global_VariableVertexNumber
		global global_FunctionVertexNumber
		global global_VertexNumber

		if vertex_type == 'v':
			self.type = 'v'
			self.vid = global_VariableVertexNumber
			global_VariableVertexNumber +=1
		elif vertex_type == 'f':
			self.type = 'f'
			self.fid = global_FunctionVertexNumber
			global_FunctionVertexNumber +=1
		else:
			raise NotImplementedError('vertex_type must be either \'v\' or \'f\' ')

		self.id = global_VertexNumber
		global_VertexNumber+=1
		self.out_edges = []

	def __str__(self):
		return 'v%s'%(str(self.id))

	def __repr__(self):
		return self.__str__()

class Edge:
	def __init__(self,source, target):
		self.source = source
		self.target = target
		
	def __str__(self):
		return '[%s,%s]'%(str(self.source), str(self.target))
	def __repr__(self):
		return self.__str__()


VertexList = []

class adouble:
	def __init__(self,x):
		self.x = x
		self.vertex = Vertex(vertex_type='v')
		VertexList.append(self.vertex)
		

	def __add__(self,rhs):
		retval = adouble(self.x + rhs.x)
		f = Vertex(vertex_type='f')
		e3 = Edge(f,retval.vertex)
		f.out_edges.append(e3)
		
		VertexList.append(f)
		e1 = Edge(self.vertex,f)
		e2 = Edge(rhs.vertex,f)
		self.vertex.out_edges.append(e1)
		rhs.vertex.out_edges.append(e2)

		return retval

ax = adouble(1.)
ay = adouble(2.)

az = ax + ay + ax + ay + ay
ax = az + ax + ay

#a = VariableNode()
#b = VariableNode()

#f = FunctionNode()
#ea = Edge(a,f)
#eb = Edge(b,f)
#a.out_edges.append(ea)
#b.out_edges.append(eb)
#print a.out_edges
#print b.out_edges

from pygraphviz import *

#A=AGraph()

## set some default node attributes
#A.node_attr['style']='filled'
#A.node_attr['shape']='circle'
#A.node_attr['fixedsize']='true'
#A.node_attr['fontcolor']='#FFFFFF'

## make a star in shades of red
#for i in range(16):
    #A.add_edge(0,i)
    #n=A.get_node(i)
    #n.attr['fillcolor']="#%2x0000"%(i*16)
    #n.attr['height']="%s"%(i/16.0+0.25)
    #n.attr['width']="%s"%(i/16.0+0.25)

#print A.string() # print to screen
#A.write("star.dot") # write to simple.dot
#print "Wrote star.dot"
#A.draw('star.png',prog="circo") # draw to png using circo
#print "Wrote star.png"

A = AGraph()
A.node_attr['style']='filled'
A.node_attr['shape']='circle'
A.node_attr['fixedsize']='true'
A.node_attr['fontcolor']='#000000'

for v in VertexList:
	for e in v.out_edges:
		print v.id,'->',e.target.id,"  :   ",v,'->',e.target
		A.add_edge(v.id,e.target.id)
		s = A.get_node(v.id)
		if v.type == 'f':
			s.attr['fillcolor']="#000000"
			s.attr['shape']='rect'
			s.attr['label']='+'
			s.attr['width']='0.3'
			s.attr['height']='0.3'
			s.attr['fontcolor']='#ffffff'

		elif v.type == 'v':
			s.attr['fillcolor']="#FFFF00"
			s.attr['shape']='circle'
			s.attr['label']= 'v_%d'%v.id
			s.attr['width']='0.3'
			s.attr['height']='0.3'

print A.string() # print to screen

A.write("computational_graph.dot")




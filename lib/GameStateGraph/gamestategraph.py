"""
TODO
- change interaction method for state to: 
		check items to perform operation on
		select a checked or unchecked node
		menu popup asks to do action
			if you select a checked node, action is performed on selected nodes
			if you select an unchecked node, action is performed on the selected node with the checked nodes as targets
		actions: move checked nodes under selected node, shuffle selected node children, shuffle checked nodes
- add states navigation
		state navigator is left column, individual state view is middle column, node details is right column
		state navigator shows id, label of each state in tree
			list of sequential states
			if there is branching, create a branch node
			select a state to open it in the middle column individual state view
			button on state to delete or create new branch
		state view shows the state tree
- save/load state tree
- nicegui exposes initial state generation
- save state change commands instead of individual states and generate entire tree
	- show states that are invalid after a state change command
"""

import itertools, copy, random

random.seed(50)
def prod(*lists):
	return [x for x in itertools.product(*lists)]
def shuffled(l):
	newl = [x for x in l]
	random.shuffle(newl)
	return newl

class Node:
	def __init__(self, name=None, children=None, compress=False, is_root=False, parent=None, **kwargs):
		self.name = name
		self.attributes = kwargs
		if not children:
			children = []
		self.children:list[Node] = children
		self.compress = compress

		self.uid:int|None = None  # Must be set at some point before used

		self.is_root = is_root  # The root node will keep track of ids as an attribute
		self.root:Node = None
		self.parent:Node = None
		if self.is_root:
			self.root = self
			self.attributes["last_id"] = 0
			self.uid = 0
			self.dirty = True

		self.recursive_update = True
		self.name_cache = {}
	def update_tree(self):
		if self.is_root:
			print("call update tree on a root", self.dirty)
			if self.dirty:
				self.dirty = False
				self._annotate_subtree()
				self.dirty = True
		elif self.root:
			self.root.update_tree()
		else:
			raise Exception("A Node should always either be the root or have a root")
	def _annotate_subtree(self):
		if not self.is_root:
			raise Exception("Only the root should call annotate_subtree")
		#print("- call annotate from "+self.fullname()+" -")
		self.name_cache[:] = {}
		for node in self.walk():
			#print("-- walking node", node.fullname(),"--")
			self.name_cache[node.fullname()] = node
			if node == self:
				continue
			node.root = self
			node.is_root = False
			if node.uid == None:
				#print("--- setting uid", self.root.attributes)
				node.uid = self.root.attributes["last_id"]+1
				self.root.attributes["last_id"]+=1
	def walk(self):
		""" Iterator to get all nodes, with depth-first search.
		Also as a side effect ensures nodes point to correct parent"""
		search_nodes = [self]
		while search_nodes:
			cur_node = search_nodes.pop()
			yield cur_node
			for child_node in cur_node.children:
				child_node.parent = cur_node
				search_nodes.append(child_node)
	def find_node(self, node_name):
		for node in self.walk():
			if node.name == node_name or node.name == node_name or node.uid == node_name:
				return node
			if isinstance(node_name, str) and '.' in node_name and node.fullname().endswith(node_name):
				return node
		return None
	def get_index(self):
		if not self.parent:
			return 0
		return self.parent.children.index(self)
	def reparent(self, parent):
		""" Moves a node from its current parent to the parent with the given name """
		self.parent.children.remove(self)
		parent.children.append(self)
		self.update_tree()
	def delete_children(self):
		self.children[:] = []
		if self.is_root:
			self.attributes["last_id"] = 0
	def randomize_children(self, child_name):
		""" Moves a node from its current parent to the parent with the given name """
		random.shuffle(self.children)
	def add_children(self, children):
		self.children.extend(children)
		print("add children", self.root.dirty)
		self.update_tree()
		return self
	def fullname(self):
		n = self.name
		p = self.parent
		while p:
			n = p.name+'.'+n
			p = p.parent
		return n
	def copy(self):
		do_update = self.recursive_update
		if do_update:
			self.recursive_update = False
		copied = copy.copy(self)
		if copied.is_root:
			copied.uid = 0
		else:
			copied.uid = None
		copied.attributes = copy.copy(self.attributes)
		if self.is_root:
			copied.attributes["last_id"] = 0
		copy_children = [copied]
		while copy_children:
			next_copy = copy_children.pop(0)
			new_children = []
			for i in range(len(next_copy.children)):
				new_children.append(next_copy.children[i].copy())
				copy_children.append(next_copy.children[i])
			next_copy.children = new_children
		if do_update:
			copied.update_tree()
			self.recursive_update = True
		return copied
	def to_dict(self):
		d = {}
		d["name"] = self.name
		d["children"] = [child.to_dict() for child in self.children]
		d["compress"] = self.compress
		d["is_root"] = self.is_root
		d["attributes"] = self.attributes
		return d
	@staticmethod
	def from_dict(d):
		n = Node(d["name"], [Node.from_dict(child_d) for child_d in d["children"]], d["compress"], d["is_root"])
		n.attributes = d["attributes"]
		if n.is_root:
			n.update_tree()
		return n
	
class Action:
	def __init__(self, owner:str, action_object:object, state:Node):
		self.owner:str = owner
		self.action_object:object = action_object
		self.state:Node = state
	def __str__(self):
		return f'{self.owner or "(system)"} performed {str(self.action_object)}'
	def copy(self):
		return Action(self.owner, self.action_object, self.state.copy())
	
class GameState(Node):
	""" A GameState contains the actual state (to keep tree roots separate) as well as a stack
	of actions that was performed on the parent game state to get to this state"""
	def __init__(self, initial_state, action_level=1):
		super().__init__()
		self.attributes["action_stack"] = []
		self.add_action(Action(None, "init", initial_state))
		self.action_level = action_level
	@property
	def current_state(self):
		return self.action_stack[-1].state
	@property
	def action_stack(self):
		return self.attributes["action_stack"]
	@property
	def name(self):
		return "state"+str(self.action_level)
	@name.setter
	def name(self, value):
		pass
	def add_action(self, action:Action):
		action.state.attributes["game_state_owner"] = self
		self.action_stack.append(action)
	def add_branch(self, branch_name:str=None):
		""" Make a new sibling clone of this state as an alternate move """
		state = self.copy()
		state.delete_children()
		print(id(self.attributes), id(state.attributes))
		if branch_name:
			state.attributes["branch_name"] = branch_name
		state.attributes["game_state_owner"] = self
		self.parent.add_children([state])
		return state
	def add_next(self):
		""" Make a new child clone of this state as the next move"""
		state = self.copy()
		state.delete_children()
		state.action_level += 1
		state.attributes["game_state_owner"] = self
		self.add_children([state])
		return state
	def copy(self):
		state = super().copy()
		state.action_stack[:] = [action.copy() for action in self.action_stack]
		return state
	
class GameStateTree(Node):
	""" A GameStateTree is a tree of GameStates.
	Each child GameState is a different decision which is made on the current state
	GameStateTree
		state1
			state2
				state3
					state4
						state5
						state6
					state4
						state5
						state6
		state1
			state2
				state3
	"""
	def __init__(self):
		super().__init__("GameStateTree", is_root=True)
	def update_tree(self):
		super().update_tree()
		for node in self.walk():
			if isinstance(node, GameState):
				node.current_state.update_tree()
	

def print_state(node):
	next = [(node,0)]
	while next:
		next_node:Node = None
		next_node, indent = next.pop(0)
		print('   '*indent + next_node.name+" - ",next_node.uid)
		for k in sorted(next_node.attributes.keys()):
			print('   '*indent + ':'+k+':'+str(next_node.attributes[k]))
		if next_node.compress and next_node.children:
			print('   '*(indent+1) + ">"+", ".join([child.name+" - "+str(next_node.uid) for child in next_node.children]))
		else: 
			for child in reversed(next_node.children):
			    next.insert(0, (child,indent+1))

def get_ui_tree(state:Node):
	d = {
		"compress":state.compress,
		"uid":state.uid, 
		"fullname": state.fullname(), 
		"name": state.name, 
		"children":[get_ui_tree(child) for child in state.children]
	}
	# Within the state explorer, don't interact with root
	if state.is_root and isinstance(state, GameStateTree):
		d["tickable"] = False
		d["selectable"] = False
	# Within a given state, only tick
	# if not isinstance(state, GameState):
	# 	d["selectable"] = False
	return d



if __name__ == "__main__":
	colors = ["green","red","blue"]
	action_numbers = [1,1,3,3,5,5,7,7,9]
	lock_numbers = [2, 3, 4, 6, 8, 10]
	loot_types = "ABC111222333"*4


	initial_state = Node("zones", is_root=True).add_children(
		[
			Node("action_deck",
			[
				Node(color+"."+str(number))
				for (color,number) in shuffled(prod(colors,action_numbers))
			], compress=True
			),
			Node("lock_deck",[
				Node("Lock-"+color+"."+str(number)) 
				for (color, number) in shuffled(prod(colors,lock_numbers))
			], compress=True),
			Node("loot_deck",[
				Node(t) for t in  shuffled(loot_types)
			], compress=True)
		] + 
		[
			Node("heist"+str(i+1),
				[
					Node("players"), Node("row", compress=True)
				]
			) for i in range(2)
		] +
		[
			Node("player"+str(i+1),
				[
					Node("hand",compress=True)
				]
			) for i in range(5)
		]
	)
	game_state = GameStateTree()
	state1a = GameState([], initial_state)
	print("* add child 1a")
	game_state.add_children([state1a])
	print("* add branch experiment")
	state1b = state1a.add_branch("experiment")
	print("* add child 2a")
	state2a = state1a.add_next()
	print("* add child 3a")
	state3a = state2a.add_next()
	print("* add child 2b")
	state2b:GameState = state1b.add_next()
	state2b.add_action(Action("move", "action_deck.red.9", "player1.hand"))
	print_state(game_state)
	print_state(state2a.current_state)
	print_state(state2b.current_state)

	#print_state(states[0])
	#print(states[0])
	#new_state = move('Lock-green.2', 'heist1.row', states[0])
	#print_state(new_state)
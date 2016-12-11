# Neural Network
#
# Author: Luke Munro
from sigNeuron import *
from BoxesDots import *
import numpy as np
import random

"""Neural net class for systems with any # of hidden layers."""

class Net(Player):
	def __init__(self, sizeIn, layerList, gridSize):
		Player.__init__(self, "AI")
		self.sizeIn = sizeIn
		self.gridSize = gridSize
		self.numLayers = len(layerList)
		self.layerList = layerList
		self.layers = [[] for x in range(self.numLayers)]
		for i in range(layerList[0]):
			self.layers[0].append(Neuron(self.sizeIn+1, i))#int(random.random()*100)))
		for i, nodes in enumerate(layerList[1:]):
			for x in range(nodes):
				self.layers[i+1].append(Neuron(len(self.layers[i])+1, x))# int(random.random()*100)))
		self.oldUpdateVector = self.getWeights()*0

	def getWeights(self): 
		layerWeights = []
		layerWeights.append(np.zeros(shape=(self.layerList[0], self.sizeIn+1)))
		for i in range(self.numLayers-1):
			layerWeights.append(np.zeros(shape=(self.layerList[i+1], self.layerList[i]+1)))
		for i, layer in enumerate(self.layers):
			for x, node in enumerate(layer):
				layerWeights[i][x] = node.getW()
		return np.asarray(layerWeights)


	def writeWeights(self):
		layerWeights = self.getWeights()
		for i, layer in enumerate(layerWeights):
			np.savetxt('{0}weight{1}.txt'.format(self.gridSize, i), layer) # one file later


	def loadWeights(self): # BREAKS IF YOU ONLY HAVE 1 NODE IN A LAYER
		loadedWeights = []
		for i in range(self.numLayers):
			loadedWeights.append(np.loadtxt('{0}weight{1}.txt'.format(self.gridSize, i)))
		for i, layer in enumerate(self.layers):
			for x, node in enumerate(layer):
				node.assignW(loadedWeights[i][x])


	def updateWeights(self, newLayerWeights):
		for i, layer in enumerate(newLayerWeights):
			np.savetxt('{0}weight{1}.txt'.format(self.gridSize, i), layer)
		self.loadWeights()

	def internalUpdateWeights(self, newLayerWeights): # IMPROVE UPDATEWEIGHTS
		return None

	def reg(self, Lambda): # CURRENTLY UNUSED 
		reg = []
		for w in self.getWeights():
			np.insert(w, 0, 0, axis=0) # DON'T REGULARIZE BIAS SET TO 0
			reg.append(Lambda * w)
		return np.asarray(reg)


	def getMove(self, data):
		a = []
		z = []
		a1 = cleanData(data)
		game_state = a1
		a.append(addBias(a1))
		for i in range(self.numLayers):
			z.append(computeZ(self.layers[i], a[i]))
			temp = sigmoid(z[i])
			a.append(addBias(temp))
		# REMOVE BIAS IN OUTPUT
		out = np.delete(a[self.numLayers], 0, axis=0)
		print out
		moves = findMoves(out)
		# print moves
		legalMoves = onlyLegal(moves, game_state)
		# print legalMoves
		nextMoves = formatMoves(legalMoves, makeCommands(self.gridSize))
		return nextMoves[0]

# ----------------------- Gradient Descent Algorithms ----------------------------------------------------------

# KEEP SEPERATE FOR NOW

	def train(self, alpha, old_state, y): # REGULARIZATION POSSIBLY 
# ----- Leave steps split for easier comprehension ------
		a = []
		z = []
		a1 = old_state # Already cleaned
		a.append(addBias(a1))
		for i in range(self.numLayers):
			z.append(computeZ(self.layers[i], a[i]))
			temp = sigmoid(z[i])
			a.append(addBias(temp))
		out = np.delete(a[self.numLayers], 0, axis=0)
		print np.hstack((y, out, out-y))
		print costMeanSquared(y, out) 
		noBiasWeights = self.getWeights()
		for i, weights in enumerate(noBiasWeights):
			noBiasWeights[i] = rmBias(weights)
		deltas = []
		# EDIT THIS IF CHANING COST FUNCTION
		initialDelta = (out - y) * sigGradient(z[len(z)-1])
		deltas.append(initialDelta)
		for x in range(self.numLayers-2, -1, -1):
			deltaIndex = (self.numLayers-2) - x
			delta = np.dot(noBiasWeights[x+1].transpose(), deltas[deltaIndex]) * sigGradient(z[x])
			deltas.append(delta)
		Grads = []
		# REORDER DELTAS FROM FIRST LAYER TO LAST			
		for i, delta in enumerate(deltas[::-1]):
			Grads.append(delta*a[i].transpose())
		updateVector = alpha*(np.asarray(Grads)) #+ self.reg(0.01))
		updatedWeights = self.getWeights() - updateVector
		self.updateWeights(updatedWeights)

# MOMENTUM

	def trainMomentum(self, alpha, old_state, y, gamma=0.9):
		a = []
		z = []
		a1 = old_state # Already cleaned
		a.append(addBias(a1))
		for i in range(self.numLayers):
			z.append(computeZ(self.layers[i], a[i]))
			temp = sigmoid(z[i])
			a.append(addBias(temp))
		out = np.delete(a[self.numLayers], 0, axis=0)
		# print np.hstack((y, out, out-y))
		# print costMeanSquared(y, out) 
		noBiasWeights = self.getWeights()
		for i, weights in enumerate(noBiasWeights):
			noBiasWeights[i] = rmBias(weights)

		deltas = []
		initialDelta = (out - y) * sigGradient(z[len(z)-1])
		deltas.append(initialDelta)
		for x in range(self.numLayers-2, -1, -1):
			deltaIndex = (self.numLayers-2) - x # THIS IS UGLY. UR UGLY. STOP TALKING TO YOURSELF
			delta = np.dot(noBiasWeights[x+1].transpose(), deltas[deltaIndex]) * sigGradient(z[x])
			deltas.append(delta)
		Grads = []
		for i, delta in enumerate(deltas[::-1]):
			Grads.append(delta*a[i].transpose())
		Grads = np.asarray(Grads)
		updateVector = gamma*self.oldUpdateVector + alpha*Grads
		# print updateVector[0][0]
		# print self.oldUpdateVector[0][0]
		updatedWeights = self.getWeights() - updateVector
		self.oldUpdateVector = updateVector
		self.updateWeights(updatedWeights)

# NESTEROV ACCELERATED GRADIENT 
	def trainNAG(self, alpha, old_state, y, gamma=0.9):
# UPDATE WEIGHTS RERUN TO GET FUTURE GRADIENT 
		a = []
		z = []
		a1 = old_state
		a.append(addBias(a1))
		futureWeights = self.getWeights() - gamma*self.oldUpdateVector
		# NEED NEW COMPUTEZ FUNCTION NOT PULLING WEIGHTS FROM NODES
		for i in range(self.numLayers): # EVERYTHING SAME SIZE STILL
			zi = np.dot(futureWeights[i], a[i]).reshape(np.size(self.layers[i]), 1)
			z.append(zi)
			temp = sigmoid(z[i])
			a.append(addBias(temp))
		out = np.delete(a[self.numLayers], 0, axis=0)
		# print np.hstack((y, out, out-y))
		# print costMeanSquared(y, out) 
		noBiasWeights = self.getWeights()
		for i, weights in enumerate(noBiasWeights):
			noBiasWeights[i] = rmBias(weights)
		deltas = []
		initialDelta = (out - y) * sigGradient(z[len(z)-1])
		deltas.append(initialDelta)		
		for x in range(self.numLayers-2, -1, -1):
			deltaIndex = (self.numLayers-2) - x
			delta = np.dot(noBiasWeights[x+1].transpose(), deltas[deltaIndex]) * sigGradient(z[x])
			deltas.append(delta)
		futureGrads = []
		for i, delta in enumerate(deltas[::-1]):
			futureGrads.append(delta*a[i].transpose())
		futureGrads = np.asarray(futureGrads)
		# GRADIENTS FOR FUTURE THETAS
		updateVector = gamma*self.oldUpdateVector + alpha*futureGrads
		updatedWeights = self.getWeights() - updateVector
		self.oldUpdateVector = updateVector
		self.updateWeights(updatedWeights)






# -------------------------- Computations -------------------------------

def computeZ(Nodes, X):
	w = np.zeros(shape=(np.size(Nodes), np.size(X)))
	for i, node in enumerate(Nodes):
		w[i] = node.getW()
	z = np.dot(w, X).reshape(np.size(Nodes), 1)
	return z

def sigmoid(z):
	return 1/(1+np.exp(-z))

def costLog(y, a):
	cost = -y * np.log10(a) - (1 - y) * np.log10(1 - a)
	return sum(cost)

def costMeanSquared(y, a):
	cost = ((a - y)**2)/2.0
	return sum(cost)

def sigGradient(z):
	return sigmoid(z) * (1 - sigmoid(z))

def estimateGradlog(y, a, weights, epsilon): # DO THIS LATER
	for i in range(weights):
		for i in range(weights[i]):
			continue
	return None
	# return (costLog(y, a+epsilon) - costLog(y, a-epsilon))


# ---------------------------- Utility ----------------------------------

def cleanData(raw):
	data = [[int(i)] for x in raw for i in x]
	data = np.array(data)
	return data
		
def addBias(aLayer): # Adds 1 to vertical vector matrix
	return np.insert(aLayer, 0, 1, axis=0)


def rmBias(weightMatrix): # removes bias weight from all nodes 
	return np.delete(weightMatrix, 0, axis=1)

# ------------------ Translating to BoxesDotes ----------------------


def findMoves(probs): # CONDENSE fix for same prob
	moves = []
	probs = probs.tolist()
	tProbs = list(probs)
	for i in range(len(probs)):
		high = max(tProbs)
		index = probs.index(high)
		probs[index] = -1 # working fix for same probs bug
		moves.append(index)
		tProbs.remove(high)
	return moves

def makeCommands(gridDim):
	moveCommands = []
	for i in range(gridDim*2+1):
		if i%2==0:
			for x in range(gridDim):
				moveCommands.append(str(i)+" "+str(x))
		else:
			for x in range(gridDim+1):
				moveCommands.append(str(i)+" "+str(x))
	return moveCommands

def formatMoves(moveOrder, commands): # CONDENSE
	fmatMoves = []
	for i, move in enumerate(moveOrder):
		fmatMoves.append(commands[move])
	return fmatMoves


def onlyLegal(moves, justMoves): # CONDENSE
	legalMoves = []
	for i in range(len(justMoves)):
		if justMoves[i] == 0:
			legalMoves.append(i)
	moveOrder = filter(lambda x: x in legalMoves, moves)
	return moveOrder

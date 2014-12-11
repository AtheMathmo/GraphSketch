from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import Property, NumericProperty, ReferenceListProperty,\
    ObjectProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Ellipse, Line
from kivy.graphics.context_instructions import PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
import math
import sys


class GraphToolBar(BoxLayout):

    nodeSize = NumericProperty(50)
    directedGraph = BooleanProperty(False)

    def add_buttons(self, game):
        self.orientation = 'vertical'
        
        createNodeButton = Button(text = 'CreateNode', size_hint = (1, .2))
        createEdgeButton = Button(text = 'CreateEdge', size_hint = (1, .2))
        updateNodeSizeButton = Button(text = 'NewSize', size_hint = (1, .2))
        slider = Slider(orientation='horizontal',value = 50,min = 25, max = 75, size_hint=(1, .1))
        directedGraphToggle = ToggleButton(text='Directed', size_hint=(1,.2), state='normal')
        clearStuffToggle = ToggleButton(text='Delete', state = 'normal')
        
        
        self.add_widget(createNodeButton)
        self.add_widget(createEdgeButton)
        self.add_widget(updateNodeSizeButton)
        self.add_widget(slider)
        self.add_widget(directedGraphToggle)
        self.add_widget(clearStuffToggle)
        
        def createNode(instance):
            newNode = GraphNode(self.nodeSize)
            game.add_widget(newNode)
            print "Node Created"

        def createEdge(instance):
            direction = 1 if self.directedGraph else 0
            newEdge = GraphEdge(self.nodeSize, direction)
            game.add_widget(newEdge)
            print "Edge Created"

        def updateNodeSize(instance):
            self.nodeSize = slider.value
            for widget in game.children:
                if isinstance(widget, GraphNode):
                    widget.update_size(self.nodeSize)
                if isinstance(widget, GraphEdge):
                    widget.update_nodeSize(self.nodeSize)

        def updateDirection(instance):
            direction = 1 if self.directedGraph else 0
            for widget in game.children:
                if isinstance(widget, GraphEdge):
                    widget.update_direction(direction)
                        
        def activateClearState(instance):
            game.clearState = (not game.clearState)
            pass

        def activateDirectedGraph(instance):
            self.directedGraph = (not self.directedGraph)
            direction = 1 if self.directedGraph else 0
            updateDirection(direction)
            pass
        
        createNodeButton.bind(on_press=createNode)
        createEdgeButton.bind(on_press=createEdge)
        updateNodeSizeButton.bind(on_press=updateNodeSize)
        clearStuffToggle.bind(on_press=activateClearState)
        directedGraphToggle.bind(on_press=activateDirectedGraph)
    pass

    

class GraphInterface(Widget): 
    node = ObjectProperty(None)
    toolbar = ObjectProperty(None)
    clearState = BooleanProperty(False)

    def update(self, dt):
        for widget in self.children:
            if isinstance(widget, GraphEdge) and widget.collide_widget(self):
                widget.check_connection()

    def construct_toolbar(self):
        self.toolbar.add_buttons(self)
        
class GraphNode(Widget):
    r = NumericProperty(1.0)
    edgeList = ListProperty([])

    def __init__(self, sizeInput=50, **kwargs):
        super(GraphNode, self).__init__(**kwargs)
        with self.canvas:
            Color(self.r,1,1,1)
            self.size= [sizeInput,sizeInput]
            self.pos = [175,125]
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            
            if self.parent.clearState:
                for edge in self.edgeList:
                    if self == edge.connected_node_0:
                        edge.connected_point_0 = False
                    elif self == edge.connected_node_1:
                        edge.connected_point_1 = False                        
                    edge.center = ((edge.line.points[0]+edge.line.points[2])/2,(edge.line.points[1]+edge.line.points[3])/2)
                    edge.size = [math.sqrt(((edge.line.points[0]-edge.line.points[2])**2 + (edge.line.points[1]-edge.line.points[3])**2))]*2
                self.parent.remove_widget(self)
                return True
            
            if touch.grab_current == None:
                self.r = 0.6
                touch.grab(self)             
                return True
        return super(GraphNode, self).on_touch_down(touch)
           
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.pos=[touch.x-25,touch.y-25]
        for widget in self.parent.children:
            if isinstance(widget, GraphEdge) and widget.check_line_widget_collision(self):
                if widget not in self.edgeList:
                    widget.snap_to_node(self)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.r = 1.0

    def update_size(self, nodeSize):
        self.size = nodeSize, nodeSize

class GraphEdge(Widget):
    # properties for updating edges
    colour = NumericProperty(1.0)
    angle = NumericProperty(0.0)
    length = NumericProperty(0.0)
    nodeSize = NumericProperty(50)
    direction = NumericProperty(0.0)
    
    # node links
    connected_point_0 = BooleanProperty(False)
    connected_point_1 = BooleanProperty(False)
    connected_node_0 = Widget()
    connected_node_1 = Widget()
    
    def __init__(self, nodeSizeInput = 50, directionInput = 0, **kwargs):
        self.nodeSize = nodeSizeInput
        self.direction = directionInput
        super(GraphEdge, self).__init__(**kwargs)
        with self.canvas:
            Color(self.colour, 1, 1, 1)
            self.line = Line(points=[100, 200, 200, 200], width = 2.0)
        with self.canvas.after:
            Color(1,0,0,1)
            self.forwardEdge = Line(points=[], width = 6)
            self.backwardEdge = Line(points=[], width = 6)           
        
    def check_line_point_collision(self, position):
        # We construct axis-lines for the bounding box, and then check that we are within this region (by finding perp distance)
        width = self.nodeSize
        length = self.update_length()
        paralellAngle = self.update_angle()
        perpAngle = paralellAngle + math.pi/2
        
        insidePerp = False
        insideParallel = False
        
        startingPoint = (self.line.points[0] + length*math.cos(paralellAngle)/2, self.line.points[1] + length*math.sin(paralellAngle)/2)

        parallelDistance = math.fabs(position[1]-math.tan(perpAngle)*position[0] - (startingPoint[1]-math.tan(perpAngle)*startingPoint[0]))/math.sqrt(1+math.tan(perpAngle)**2)
        insideParallel = parallelDistance < length/2

        perpDistance = math.fabs(position[1]-math.tan(paralellAngle)*position[0] - (startingPoint[1]-math.tan(paralellAngle)*startingPoint[0]))/math.sqrt(1+math.tan(paralellAngle)**2)
        insidePerp = perpDistance < width/2
        
        return (insidePerp and insideParallel)

    def check_line_widget_collision(self, wid):
        ## if not axis-aligned, corners will break first. Might need to classify by angle of line...

        widgetCollision = False
        #(botLeft,botRight,topLeft,topRight)
        widCorners = ((wid.x,wid.y),(wid.x+wid.size[0],wid.y),(wid.x,wid.y + wid.size[1]),(wid.x+wid.size[0],wid.y+wid.size[1]))
        for corner in widCorners:
            widgetCollision = widgetCollision or self.check_line_point_collision(corner)
        return widgetCollision
        
        return True
    def update_angle(self):
        self.angle = math.atan2((self.line.points[3]-self.line.points[1]),(self.line.points[2]-self.line.points[0]))
        return self.angle

    def update_length(self):
        self.length = math.sqrt(((self.line.points[0]-self.line.points[2])**2 + (self.line.points[1]-self.line.points[3])**2))
        return self.length

    def update_nodeSize(self, newSize):
        self.nodeSize = newSize
        pass

    def update_direction(self, newDirection):
        self.direction = newDirection
        pass
        
    def on_touch_down(self, touch):
        if self.check_line_point_collision(touch.pos):
            if self.parent.clearState:
                self.parent.remove_widget(self)
                return True
            if self.direction > 0 and self.direction < 4:
                self.direction += 1
            if self.direction == 4:
                self.direction = 1
        return super(GraphEdge, self).on_touch_down(touch)
        
    def snap_to_node(self, node):            

        distance_from_0 = [math.sqrt(((self.line.points[0]-node.center[0])**2 + (self.line.points[1]-node.center[1])**2))]*2
        distance_from_1 = [math.sqrt(((self.line.points[2]-node.center[0])**2 + (self.line.points[3]-node.center[1])**2))]*2
        
        if distance_from_0 <= distance_from_1:
            if (self.connected_point_0 is False):
                print "collision"                
                if node is not self.connected_node_1:
                    self.connected_point_0 = True
                    self.connected_node_0 = node
                    node.edgeList.append(self)
                    self.line.points = node.center + self.line.points[2:]
                    
        elif distance_from_1 < distance_from_0:
            if (self.connected_point_1 is False):
                print "collision"
                if node is not self.connected_node_0:
                    self.connected_point_1 = True
                    self.connected_node_1 = node
                    node.edgeList.append(self)
                    self.line.points =  self.line.points[:-2] + node.center
        return True

    def check_connection(self):
        if self.connected_point_0:
            self.line.points = self.connected_node_0.center + self.line.points[2:] 
            #self.center = [self.line.points[0]+(self.update_length()/2),self.line.points[1]]    
            #self.size = [self.update_length(), self.nodeSize/2]
            self.colour = self.connected_node_0.r
            if self.direction == 1 or self.direction == 3:              
                self.update_angle()
                self.backwardEdge.points = [self.line.points[0]+(self.nodeSize/2)*math.cos(self.angle),self.line.points[1]+(self.nodeSize/2)*math.sin(self.angle),self.line.points[0] + (self.update_length()*1/10+self.nodeSize/2)*math.cos(self.angle), self.line.points[1] + (self.update_length()*1/10+self.nodeSize/2)*math.sin(self.angle)]
            elif self.direction == 0 or self.direction == 2:
                self.backwardEdge.points = []
            
        if self.connected_point_1:
            self.line.points = self.line.points[:2] + self.connected_node_1.center
            #self.center = [self.line.points[0]+(self.update_length()/2),self.line.points[1]]    
            #self.size = [self.update_length(), self.nodeSize/2]
            self.colour = self.connected_node_1.r
            if self.direction == 2 or self.direction == 3:              
                self.update_angle()
                self.forwardEdge.points = [self.line.points[0]+(self.update_length()*9/10-self.nodeSize/2)*math.cos(self.angle),self.line.points[1]+(self.update_length()*9/10-self.nodeSize/2)*math.sin(self.angle),self.line.points[0] + (self.update_length()-self.nodeSize/2)*math.cos(self.angle), self.line.points[1] + (self.update_length()-self.nodeSize/2)*math.sin(self.angle)]
            elif self.direction == 0 or self.direction == 1:
                self.forwardEdge.points = []
        if self.connected_point_0 and self.connected_point_1:
            #self.center = [self.line.points[0]+(self.update_length()/2),self.line.points[1]]    
            #self.size = [self.update_length(), self.nodeSize/2]
            pass
            
            
            

class GraphApp(App):
   
    def build(self):
        game = GraphInterface()
        
        game.construct_toolbar()
        
        Clock.schedule_interval(game.update, 1.0/20.0)  
        return game

if __name__ == '__main__':

    GraphApp().run()

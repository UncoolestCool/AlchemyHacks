import pygame
from misc.textures import TextureAtlas
from misc import events

class Item:
    def __init__(self, itemid, tex_name, stackable=True):
        self.itemid = itemid
        self.tex_name = tex_name
        self.stackable = stackable

        self._atlas_given = False

    def addToGroup(self, group):
        group.append(self)

    def register(self, registry):
        registry.addItem(self)

    def setAtlas(self, atlas):
        self.atlas = atlas

        self.tex_loc = self.atlas.getTextureLoc(self.tex_name)

        self._atlas_given = True

    def isStackable(self):
        return self.stackable

    def getItemID(self):
        return self.itemid
    
    def onLeft(self, player, world, tile, tile_pos): pass
    def onRight(self, player, world, tile, tile_pos): pass
    def onMiddle(self, player, world, tile, tile_pos): pass

    def draw(self, surface, center):
        if self._atlas_given:
            item_drawing_bounds = pygame.Rect((0, 0), self.atlas.getTextureSize())
            item_drawing_bounds.center = center

            self.atlas.drawTextureAtLoc(surface, item_drawing_bounds.topleft, self.tex_loc)

class ItemStack:
    REGISTRY = None
    ITEM_COUNTER_FONT = pygame.font.SysFont("Courier New", 40)
    
    def __init__(self, itemid, count):
        self.item = self.REGISTRY.getItem(itemid)
        self.count = count

    @classmethod
    def setRegistry(self, registry):
        self.REGISTRY = registry

    def getItemID(self):
        return self.item.getItemID()

    def getCount(self):
        return self.count

    def isEmpty(self):
        return self.getCount()==0

    def setCount(self, count):
        self.count = count

    def isStackableWith(self, stack):
        if stack == None:
            return False
        
        if not self.item.isStackable():
            return False
        if not stack.item.isStackable():
            return False
        
        if self.getItemID() != stack.getItemID():
            return False

        return True

    def stackWith(self, stack):
        if self.isStackableWith(stack):
            self.count += stack.count

            return True

        else:
            return False

    def duplicateStack(self):
        new_stack = self.__class__(self.getItemID(), self.getCount())

        return new_stack

    def draw(self, surface, center):
        self.item.draw(surface, center)
        
        stack_amount = self.ITEM_COUNTER_FONT.render(str(self.count), True, (255, 255, 255))
        surface.blit(stack_amount, center)
        

class Inventory(events.EventAcceptor):
    def __init__(self, size, width, grid_size):
        self.size = size
        self.width = width
        self.height = round(self.size/self.width+0.4999999999)
        self.grid_size = grid_size

        self.active_stack = None

        self.item_stacks = [None] * self.size

    def setItemStack(self, stack, loc):
        self.item_stacks[loc] = stack

    def addItemStack(self, stack):
        added = False
        
        for stack_loc in range(self.size):
            if self.getItemStack(stack_loc) == None:
                self.setItemStack(stack, stack_loc)
                added = True
                break

        if not added:
            self.active_stack = stack

    def getItemStack(self, loc):
        return self.item_stacks[loc]

    def isActiveStackClear(self):
        return self.getActiveStack() == None

    def isStackClear(self, loc):
        return self.getItemStack(loc) == None

    def getActiveStack(self):
        return self.active_stack

    def setActiveStack(self, stack):
        self.active_stack = stack

    def swapActiveWithStack(self, loc):
        temp = self.getActiveStack()
        self.setActiveStack(self.getItemStack(loc))
        self.setItemStack(temp, loc)

    def stackActiveWithStack(self, loc):
        stack = self.getItemStack(loc)

        if stack == None:
            self.swapActiveWithStack(loc)

        else:
            if stack.stackWith(self.getActiveStack()):
                self.setActiveStack(None)

            else:
                self.swapActiveWithStack(loc)

    def splitStackIntoActive(self, loc):
        # Get the current stack
        stack = self.getItemStack(loc)
        total_count = stack.getCount()

        # Calculate the amount before and after split
        remaining_count = total_count//2
        active_count = total_count - remaining_count

        if active_count > 0:
            active_stack = stack.duplicateStack()
            active_stack.setCount(active_count)
            self.setActiveStack(active_stack)
        
        if remaining_count > 0:            
            stack.setCount(remaining_count)
        else:
            self.setItemStack(None, loc)

    def getPosOfStack(self, loc, topleft):
        # Grid position of item stack
        grid = [0, 0]
        grid[0] = loc %  self.width
        grid[1] = loc // self.width

        # Position of item stack relative to square one
        rel_pos = [0, 0]
        rel_pos[0] = grid[0]*self.grid_size[0]
        rel_pos[1] = grid[1]*self.grid_size[1]

        # Position of item stack relative to top left of inventory
        rel_pos[0] += self.grid_size[0] // 2
        rel_pos[1] += self.grid_size[1] // 2

        # Absolute position of item stack
        pos = [0, 0]
        pos[0] = rel_pos[0] + topleft[0]
        pos[1] = rel_pos[1] + topleft[1]

        return pos

    def onMouseDown(self, ipos, button):
        # If mouse click outside of inventory bounds, quit
        if (ipos[0] < 0) or (ipos[1] < 0):
            return False
        if (ipos[0] >= self.width*self.grid_size[0]) or (ipos[1] >= self.height*self.grid_size[1]):
            return False

        # Get stack clicked on
        grid = [0, 0]
        grid[0] = ipos[0]//self.grid_size[0]
        grid[1] = ipos[1]//self.grid_size[1]

        stack_loc = grid[0] + self.width*grid[1]

        if stack_loc >= self.size:
            return False

        # If a split is possible, split, otherwise swap stack and active
        if button == pygame.BUTTON_RIGHT and self.isActiveStackClear() and not self.isStackClear(stack_loc):
            self.splitStackIntoActive(stack_loc)

        else:
            # Bring it to the active stack
            self.stackActiveWithStack(stack_loc)
        
        return True

    def close(self):
        self.addItemStack(self.active_stack)
        self.setActiveStack(None)

    def draw(self, surface, topleft):
        for stack_loc in range(self.size):
            pos = self.getPosOfStack(stack_loc, topleft)
            
            pygame.draw.circle(surface, (100, 50, 50), pos, 40)

            stack = self.getItemStack(stack_loc)
            if stack:
                stack.draw(surface, pos)

    def drawActiveStack(self, surface, pos):
        if self.getActiveStack() != None:
            self.getActiveStack().draw(surface, pos)

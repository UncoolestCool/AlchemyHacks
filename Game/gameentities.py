import pygame
import numpy as np
import os

import events
from textures import TextureAtlas, getAllXFilesInFolder
from gameitems import Inventory, ItemStack

ASSETS = os.path.join("assets", "game")

def initialiseEntities():
    registerAllEntities()
    REGISTRY.loadAtlas()

def registerAllEntities():
    REGISTRY.registerEntityClass(Player)
    REGISTRY.registerEntityClass(TestCreature)

class EntityRegistry:
    def __init__(self):
        self.entity_classes = []

        self.assets_needed = []

        self._atlas_loaded = False

    def loadAtlas(self):
        self.atlas = TextureAtlas(os.path.join(ASSETS, "entities"),
                                  ".png",
                                  (64, 64),
                                  self.assets_needed,
                                  True,
                                  True)

        self._atlas_loaded = True

        self.loadAtlasToEntities()

    def loadAtlasToEntities(self):
        if not self._atlas_loaded:
            raise RuntimeError("Entity registry texture atlas not loaded yet")
        
        for entity in self.entity_classes:
            entity.setAtlas(self.atlas)

    def registerEntityClass(self, entity):
        self.entity_classes.append(entity)
        
        assets = entity.getNeededAssets()
        self.assets_needed += assets

REGISTRY = EntityRegistry()

class Entity(events.EventAcceptor):
    def __init__(self):
        self.pos = [0, 0]

        self.cooldowns = {}

    def setWorld(self, world):
        self.world = world

    def getPos(self):
        return self.pos

    def setPos(self, pos):
        self.pos = pos

    @staticmethod
    def getNeededAssets():
        return tuple()

    # All entities of the same class share the same textures, but are loaded in different places
    @classmethod
    def setAtlas(cls, atlas):
        cls.atlas = atlas

    def kill(self):
        self.world.removeEntity(self)

    def getBufferPos(self):
        return self.world.tilePosToBufferPos(self.pos)

    def registerCooldown(self, cooldown, frames):
        self.cooldowns[cooldown] = frames

    def isCooldownActive(self, cooldown):
        return self.cooldowns.get(cooldown, False)

    def tick(self):
        for cooldown in self.cooldowns.keys():
            self.cooldowns[cooldown] -= 1
        
    def draw(self, surface): pass

class Creature(Entity):
    def __init__(self, health):
        super().__init__()
        
        self.max_health = health
        self.health = health

    def changeHealth(self, delta):
        self.health += delta

    def calcDamageModifiers(self, damage):
        return damage # No changes to damage, can be overridden for entities with armor



INITIAL_PLAYER_HEALTH = 10

class Player(Creature):    
    def __init__(self):
        super().__init__(INITIAL_PLAYER_HEALTH)

        self.loadHUD()
        self.loadInventory()

        self.disp = False

    def loadHUD(self):
        self.HUD = PlayerHUD(self)

    def loadInventory(self):
        self.inventory = Inventory(27, 8, (100, 100))
        self.inventory.setItemStack(ItemStack("lil_sword", 45), 10)
        self.inventory.setItemStack(ItemStack("epic_sword", 35), 11)
        self.inventory.setItemStack(ItemStack("cool_sword", 12), 12)

    @staticmethod
    def getNeededAssets():
        return ["player1"]

    def setManager(self, manager):
        self.manager = manager

    def tick(self):
        super().tick()
        
        self.handleMotion()

    def handleMotion(self):
        if self.isCooldownActive("movement_input"):
            return

        self.prev_pos = [self.pos[0], self.pos[1]]
        
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            self.pos[1] -= 1
        if pressed[pygame.K_a]:
            self.pos[0] -= 1
        if pressed[pygame.K_s]:
            self.pos[1] += 1
        if pressed[pygame.K_d]:
            self.pos[0] += 1

        self.disp = pressed[pygame.K_ESCAPE]

        if not self.world.isTileValidForWalking(self.pos):
            self.pos = self.prev_pos

        self.registerCooldown("movement_input", 0)

    def onMouseDown(self, pos, button):
        # If anything uses the button, player will hog mouse input
        used = 0
        
        used += int(self.HUD.onMouseDown(pos, button))
        
        return bool(used)

    def worldClosed(self):
        self.inventory.close()
        
    def kill(self):
        pygame.event.post(pygame.event.Event(events.RETURN_TO_MAIN_MENU))
            
    def getMapDelta(self):
        bpos = self.getBufferPos()
        return (-bpos[0], -bpos[1])

    def damage(self, damage):
        self.true_damage = self.calcDamageModifiers(damage)

        self.changeHealth(-self.true_damage)

        if self.health <= 0:
            self.kill()

    def getHealth(self):
        return self.health

    def getHealthPercentage(self):
        return self.health/self.max_health

    def draw(self, surface):
        # Draw player sprite
        pos = self.manager.bufferPosToScreenPos(self.getBufferPos())
        self.atlas.drawTexture(surface, pos, "player1")

        # Draw GUI
        self.HUD.draw(surface)

class PlayerHUD(events.EventAcceptor):
    HEALTH_BAR_BOUNDS = pygame.Rect((10, 10), (500, 20))
    INVENTORY_POS = (1600, 100)
    
    def __init__(self, player):
        self.player = player

    def onMouseDown(self, pos, button):
        used = 0
        
        # Inventory
        ipos = [pos[0], pos[1]]
        ipos[0] -= self.INVENTORY_POS[0]
        ipos[1] -= self.INVENTORY_POS[1]

        used += int(self.player.inventory.onMouseDown(ipos, button))

        return bool(used)

    def drawHealthBar(self, surface):
        bar = self.HEALTH_BAR_BOUNDS

        # Background
        pygame.draw.rect(surface, (128, 128, 128), bar)

        # Health stats
        pygame.draw.rect(surface, (255, 0, 0), pygame.Rect(bar.topleft, (bar.width*self.player.getHealthPercentage(), bar.height)))

    def drawInventory(self, surface):
        mouse_pos = pygame.mouse.get_pos()

        self.player.inventory.draw(surface, self.INVENTORY_POS)
        self.player.inventory.drawActiveStack(surface, mouse_pos)        
        
    def draw(self, surface):
        self.drawHealthBar(surface)
        self.drawInventory(surface)


class TestCreature(Creature):
    def __init__(self):
        super().__init__(10)

    @staticmethod
    def getNeededAssets():
        return ["enemy1"]

    def draw(self, surface):
        self.atlas.drawTexture(surface, self.world.tilePosToBufferPos(self.pos), "enemy1")
        

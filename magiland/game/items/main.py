import pygame
import numpy as np
import os

from misc import events
from misc.textures import TextureAtlas

from . import registry
from .classes import *

        
def initialiseItems():
    REGISTRY = registry.ItemRegistry()
    REGISTRY.loadAtlas()

    ItemStack.setRegistry(REGISTRY)
    
    registry.registerAllItems(REGISTRY)

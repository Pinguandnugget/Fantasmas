package com.potitosafio.fantasmas;

import net.minecraft.util.Identifier;
import software.bernie.geckolib.model.GeoModel;

public class GhostModel extends GeoModel<GhostEntity> {
 @Override public Identifier getModelResource(GhostEntity entity) { return FantasmasMod.id("geo/fantasma_" + entity.ghostColor() + ".geo.json"); }
 @Override public Identifier getTextureResource(GhostEntity entity) { return FantasmasMod.id("textures/entity/fantasma_" + entity.ghostColor() + ".png"); }
 @Override public Identifier getAnimationResource(GhostEntity entity) { return FantasmasMod.id("animations/fantasma_" + entity.ghostColor() + ".animation.json"); }
}

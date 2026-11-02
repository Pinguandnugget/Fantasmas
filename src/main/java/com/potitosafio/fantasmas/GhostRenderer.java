package com.potitosafio.fantasmas;

import net.minecraft.client.render.entity.EntityRendererFactory;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

public class GhostRenderer extends GeoEntityRenderer<GhostEntity> {
 public GhostRenderer(EntityRendererFactory.Context context) {
  super(context, new GhostModel());
  this.shadowRadius = 0.25f;
 }
}

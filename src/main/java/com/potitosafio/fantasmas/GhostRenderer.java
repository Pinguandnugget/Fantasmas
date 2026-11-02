package com.potitosafio.fantasmas;

import net.minecraft.client.render.entity.MobEntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.client.render.entity.model.EntityModelLayers;
import net.minecraft.util.Identifier;

/** Temporary vanilla biped renderer: prevents null renderer crash.
 * Blockbench/GeckoLib models are NOT integrated in this version. */
public class GhostRenderer extends MobEntityRenderer<GhostEntity, BipedEntityModel<GhostEntity>> {
    private final Identifier texture;
    public GhostRenderer(EntityRendererFactory.Context context, String color) {
        super(context, new BipedEntityModel<>(context.getPart(EntityModelLayers.ZOMBIE)), 0.3f);
        texture = FantasmasMod.id("textures/entity/fantasma_" + color + ".png");
    }
    @Override public Identifier getTexture(GhostEntity entity) { return texture; }
}

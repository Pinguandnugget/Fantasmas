package com.potitosafio.fantasmas;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;

public class FantasmasClient implements ClientModInitializer {
    @Override public void onInitializeClient() {
        FantasmasMod.GHOSTS.forEach((color, type) ->
            EntityRendererRegistry.register(type, context -> new GhostRenderer(context, color)));
    }
}

package com.potitosafio.fantasmas;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.entity.attribute.DefaultAttributeRegistry;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.mob.PathAwareEntity;
import net.minecraft.entity.ai.goal.ActiveTargetGoal;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.item.SpawnEggItem;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.minecraft.server.command.CommandManager;
import net.minecraft.text.Text;
import java.util.LinkedHashMap;
import java.util.Map;

public class FantasmasMod implements ModInitializer {
 public static final String ID = "fantasmas";
 public static boolean walls = true, terror = true;
 public static final Map<String, EntityType<GhostEntity>> GHOSTS = new LinkedHashMap<>();
 public static final Map<String, Item> ESSENCES = new LinkedHashMap<>();
 public static Identifier id(String path) { return Identifier.of(ID, path); }
 @Override public void onInitialize() {
  String[] colors = {"blanco", "amarillo", "rojo", "negro"};
  int[] eggColors = {0xEEEEEE,0xFFD23B,0xC02020,0x161616};
  for(int i=0;i<colors.length;i++) {
   String color=colors[i];
   EntityType<GhostEntity> entity = Registry.register(Registries.ENTITY_TYPE,id("fantasma_"+color),
     EntityType.Builder.<GhostEntity>create((type,world)->new GhostEntity(type,world,color), SpawnGroup.MONSTER)
       .dimensions(0.8f,1.5f).maxTrackingRange(8).build("fantasma_"+color));
   GHOSTS.put(color,entity);
   FabricDefaultAttributeRegistry.register(entity, GhostEntity.attributes());
   Item essence=Registry.register(Registries.ITEM,id("esencia_"+color),new Item(new Item.Settings()));
   ESSENCES.put(color,essence);
   Registry.register(Registries.ITEM,id("fantasma_"+color+"_spawn_egg"),
     new SpawnEggItem(entity,eggColors[i],0x444444,new Item.Settings()));
  }
  ItemGroupEvents.modifyEntriesEvent(ItemGroups.SPAWN_EGGS).register(entries -> {
   for(String c:colors) entries.add(Registries.ITEM.get(id("fantasma_"+c+"_spawn_egg")));
  });
  ItemGroupEvents.modifyEntriesEvent(ItemGroups.INGREDIENTS).register(entries -> ESSENCES.values().forEach(entries::add));
  CommandRegistrationCallback.EVENT.register((dispatcher,registryAccess,environment)->{
   dispatcher.register(CommandManager.literal("fantasmas").requires(s->s.hasPermissionLevel(2))
    .then(CommandManager.literal("atravesar")
      .then(CommandManager.literal("on").executes(ctx->{walls=true;ctx.getSource().sendFeedback(()->Text.literal("Fantasmas negros: atravesar ON"),true);return 1;}))
      .then(CommandManager.literal("off").executes(ctx->{walls=false;ctx.getSource().sendFeedback(()->Text.literal("Fantasmas negros: atravesar OFF"),true);return 1;})))
    .then(CommandManager.literal("terror")
      .then(CommandManager.literal("on").executes(ctx->{terror=true;ctx.getSource().sendFeedback(()->Text.literal("Terror ON (efectos visuales pendientes)"),true);return 1;}))
      .then(CommandManager.literal("off").executes(ctx->{terror=false;ctx.getSource().sendFeedback(()->Text.literal("Terror OFF"),true);return 1;}))));
  });
 }
}

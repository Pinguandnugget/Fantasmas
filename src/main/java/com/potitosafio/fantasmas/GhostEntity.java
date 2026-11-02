package com.potitosafio.fantasmas;

import net.minecraft.entity.EntityType;
import net.minecraft.entity.EntityData;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.mob.PathAwareEntity;
import net.minecraft.entity.ai.goal.ActiveTargetGoal;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.World;
import net.minecraft.util.math.Vec3d;

public class GhostEntity extends PathAwareEntity implements software.bernie.geckolib.animatable.GeoEntity {
private final software.bernie.geckolib.animatable.instance.AnimatableInstanceCache animationCache = software.bernie.geckolib.util.GeckoLibUtil.createInstanceCache(this);
 public String ghostColor() { return color; }
 @Override public software.bernie.geckolib.animatable.instance.AnimatableInstanceCache getAnimatableInstanceCache() { return animationCache; }
 @Override public void registerControllers(software.bernie.geckolib.animation.AnimatableManager.ControllerRegistrar controllers) {
  controllers.add(new software.bernie.geckolib.animation.AnimationController<>(this, "ghost_controller", 5, state -> {
   state.getController().setAnimation(software.bernie.geckolib.animation.RawAnimation.begin().thenLoop("animation.fantasmas.volando"));
   return software.bernie.geckolib.animation.PlayState.CONTINUE;
  }));
 }
 private final String color;
 public GhostEntity(EntityType<? extends PathAwareEntity> type, World world, String color) {
  super(type,world);this.color=color;setNoGravity(true);
 }
 public static DefaultAttributeContainer.Builder attributes() {
  return createMobAttributes().add(EntityAttributes.GENERIC_MAX_HEALTH,40.0)
    .add(EntityAttributes.GENERIC_ATTACK_DAMAGE,4.0)
    .add(EntityAttributes.GENERIC_MOVEMENT_SPEED,0.28)
    .add(EntityAttributes.GENERIC_FOLLOW_RANGE,24.0);
 }
 @Override protected void initGoals() {
  this.goalSelector.add(2,new MeleeAttackGoal(this,1.0,true));
  this.goalSelector.add(7,new WanderAroundFarGoal(this,0.7));
  this.goalSelector.add(8,new LookAtEntityGoal(this,PlayerEntity.class,10));
  this.targetSelector.add(2,new ActiveTargetGoal<>(this,PlayerEntity.class,true));
 }
 @Override public void tick() {
  super.tick();setNoGravity(true);
  // Prototipo de vuelo: corrección vertical hacia el objetivo; navegación 3D completa pendiente.
  if(!getWorld().isClient && getTarget()!=null) {
   Vec3d delta=getTarget().getPos().add(0,0.8,0).subtract(getPos());
   if(delta.lengthSquared()>1) {
    double factor=color.equals("rojo")?0.085:color.equals("negro")?0.070:color.equals("amarillo")?0.045:0.025;
    setVelocity(getVelocity().multiply(0.92).add(delta.normalize().multiply(factor)));
    velocityDirty=true;
   }
  }
  // Atravesar bloques requiere navegación y control de colisiones dedicado.
 }
 @Override public void onDeath(DamageSource source) {
  if(!getWorld().isClient && random.nextFloat()<0.25f) {
   var essence=FantasmasMod.ESSENCES.get(color);
   if(essence!=null) dropStack(new ItemStack(essence));
  }
  super.onDeath(source);
 }
}

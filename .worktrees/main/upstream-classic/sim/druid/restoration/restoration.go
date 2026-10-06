package restoration

import (
	"time"

	"github.com/wowsims/classic/sim/core"
	"github.com/wowsims/classic/sim/core/proto"
	"github.com/wowsims/classic/sim/druid"
)

// Canonical Forever spell IDs (level-60 ranks).
const (
	spellIDHealingTouch = 9888  // Healing Touch rank 12
	spellIDRejuvenation = 9840  // Rejuvenation rank 11
	spellIDRegrowth     = 9857  // Regrowth rank 11
	spellIDTranquility  = 9862  // Tranquility rank 11
	spellIDSwiftmend    = 18562 // Swiftmend rank 6
	spellIDLifebloom    = 409824
	spellIDWildGrowth   = 408120
)

// 1.12/SoD-era flat base values (this fork has no druid spell power; scaling
// comes from the talents below). Per-tick values for HoTs are total/4 ticks.
const (
	healTouchBaseLow  = 1457.0
	healTouchBaseHigh = 1709.0

	rejuPerTick = 380.0 // 1518 / 4
	regroPerTick = 518.0 // 2074 / 4

	tranqAbsorb = 1857.0

	lifebloomInstant = 1471.0
	lifebloomPerTick = 380.0 // 1518 / 4

	wildGrowthLow  = 2012.0
	wildGrowthHigh = 2364.0
)

func RegisterRestorationDruid() {
	core.RegisterAgentFactory(
		proto.Player_RestorationDruid{},
		proto.Spec_SpecRestorationDruid,
		func(character *core.Character, options *proto.Player) core.Agent {
			return NewRestorationDruid(character, options)
		},
		func(player *proto.Player, spec interface{}) {
			playerSpec, ok := spec.(*proto.Player_RestorationDruid)
			if !ok {
				panic("Invalid spec value for Restoration Druid!")
			}
			player.Spec = playerSpec
		},
	)
}

func NewRestorationDruid(character *core.Character, options *proto.Player) *RestorationDruid {
	restoOptions := options.GetRestorationDruid()
	selfBuffs := druid.SelfBuffs{}

	resto := &RestorationDruid{
		Druid: druid.New(character, druid.Humanoid, selfBuffs, options.TalentsString),
	}

	resto.SelfBuffs.InnervateTarget = &proto.UnitReference{}
	if restoOptions != nil && restoOptions.Options != nil && restoOptions.Options.InnervateTarget != nil {
		resto.SelfBuffs.InnervateTarget = restoOptions.Options.InnervateTarget
	}

	return resto
}

type RestorationDruid struct {
	*druid.Druid

	HealingTouch *druid.DruidSpell
	Rejuvenation *druid.DruidSpell
	Regrowth     *druid.DruidSpell
	Tranquility  *druid.DruidSpell
	Swiftmend    *druid.DruidSpell
	Lifebloom    *druid.DruidSpell
	WildGrowth   *druid.DruidSpell
}

func (resto *RestorationDruid) GetDruid() *druid.Druid {
	return resto.Druid
}

func (resto *RestorationDruid) Initialize() {
	resto.Druid.Initialize()
	resto.RegisterRestorationSpells()
}

func (resto *RestorationDruid) Reset(sim *core.Simulation) {
	resto.Druid.Reset(sim)
}

func (resto *RestorationDruid) RegisterRestorationSpells() {
	resto.registerHealingTouch()
	resto.registerRejuvenation()
	resto.registerRegrowth()
	resto.registerTranquility()
	resto.registerSwiftmend()
	resto.registerLifebloom()
	resto.registerWildGrowth()
}

// healingPowerMultiplier applies the shared holy/arcane healing talents.
func (resto *RestorationDruid) healingPowerMultiplier() float64 {
	return 1 *
		(1 + .05*float64(resto.Talents.GiftOfNature)) *
		(1 + .02*float64(resto.Talents.TranquilSpirit))
}

func (resto *RestorationDruid) registerHealingTouch() {
	resto.HealingTouch = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDHealingTouch},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.55},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: time.Second * 1500}},

		DamageMultiplier: resto.healingPowerMultiplier() * (1 + .05*float64(resto.Talents.ImprovedHealingTouch)),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(healTouchBaseLow, healTouchBaseHigh)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)
		},
	})
}

func (resto *RestorationDruid) registerRejuvenation() {
	resto.Rejuvenation = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDRejuvenation},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.35},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: 1,
		ThreatMultiplier: 1,

		Hot: core.DotConfig{
			Aura: core.Aura{
				Label:    "Rejuvenation",
				ActionID: core.ActionID{SpellID: spellIDRejuvenation},
			},
			NumberOfTicks: 4,
			TickLength:    time.Second * 4,
			OnSnapshot: func(sim *core.Simulation, target *core.Unit, dot *core.Dot, _ bool) {
				dot.SnapshotBaseDamage = rejuPerTick * resto.healingPowerMultiplier() * (1 + .05*float64(resto.Talents.ImprovedRejuvenation))
				dot.SnapshotAttackerMultiplier = 1
			},
			OnTick: func(sim *core.Simulation, target *core.Unit, dot *core.Dot) {
				dot.CalcAndDealPeriodicSnapshotHealing(sim, target, dot.OutcomeTick)
			},
		},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			spell.Hot(target).Apply(sim)
		},
	})
}

func (resto *RestorationDruid) registerRegrowth() {
	resto.Regrowth = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDRegrowth},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.45},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: 1,
		ThreatMultiplier: 1,

		Hot: core.DotConfig{
			Aura: core.Aura{
				Label:    "Regrowth",
				ActionID: core.ActionID{SpellID: spellIDRegrowth},
			},
			NumberOfTicks: 4,
			TickLength:    time.Second * 4,
			OnSnapshot: func(sim *core.Simulation, target *core.Unit, dot *core.Dot, _ bool) {
				dot.SnapshotBaseDamage = regroPerTick * resto.healingPowerMultiplier() * (1 + .05*float64(resto.Talents.ImprovedRegrowth))
				dot.SnapshotAttackerMultiplier = 1
			},
			OnTick: func(sim *core.Simulation, target *core.Unit, dot *core.Dot) {
				dot.CalcAndDealPeriodicSnapshotHealing(sim, target, dot.OutcomeTick)
			},
		},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			spell.Hot(target).Apply(sim)
		},
	})
}

func (resto *RestorationDruid) registerTranquility() {
	resto.Tranquility = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDTranquility},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.55},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: resto.healingPowerMultiplier() * (1 + .15*float64(resto.Talents.ImprovedTranquility)),
		ThreatMultiplier: 1,

		Shield: core.ShieldConfig{Aura: core.Aura{Label: "Tranquility", Duration: time.Second * 15}},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			shield := spell.Shield(target)
			shield.Apply(sim, tranqAbsorb)
		},
	})
}

func (resto *RestorationDruid) registerSwiftmend() {
	resto.Swiftmend = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDSwiftmend},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.45},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: 2500 * time.Millisecond}},

		DamageMultiplier: resto.healingPowerMultiplier(),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			// Swiftmend converts all of the target's existing healing-over-time
			// effects into instant healing equal to their remaining value.
			total := 0.0
			convert := func(sp *druid.DruidSpell, perTick float64) {
				if sp == nil {
					return
				}
				hot := sp.Hot(target)
				if hot == nil || !hot.IsActive() {
					return
				}
				remaining := hot.OriginalNumberOfTicks - hot.TickCount
				if remaining < 0 {
					remaining = 0
				}
				total += float64(remaining) * hot.SnapshotBaseDamage * hot.SnapshotAttackerMultiplier
				hot.Deactivate(sim)
			}
			convert(resto.Rejuvenation, rejuPerTick)
			convert(resto.Regrowth, regroPerTick)
			convert(resto.Lifebloom, lifebloomPerTick)
			spell.CalcAndDealHealing(sim, target, total, spell.OutcomeHealingCrit)
		},
	})
}

func (resto *RestorationDruid) registerLifebloom() {
	resto.Lifebloom = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDLifebloom},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.45},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: resto.healingPowerMultiplier(),
		ThreatMultiplier: 1,

		Hot: core.DotConfig{
			Aura: core.Aura{
				Label:    "Lifebloom",
				ActionID: core.ActionID{SpellID: spellIDLifebloom},
			},
			NumberOfTicks: 4,
			TickLength:    time.Second * 4,
			OnSnapshot: func(sim *core.Simulation, target *core.Unit, dot *core.Dot, _ bool) {
				dot.SnapshotBaseDamage = lifebloomPerTick * resto.healingPowerMultiplier()
				dot.SnapshotAttackerMultiplier = 1
			},
			OnTick: func(sim *core.Simulation, target *core.Unit, dot *core.Dot) {
				dot.CalcAndDealPeriodicSnapshotHealing(sim, target, dot.OutcomeTick)
			},
		},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			spell.CalcAndDealHealing(sim, target, lifebloomInstant, spell.OutcomeHealingCrit)
			spell.Hot(target).Apply(sim)
		},
	})
}

func (resto *RestorationDruid) registerWildGrowth() {
	resto.WildGrowth = resto.RegisterSpell(druid.Humanoid, core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDWildGrowth},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType:   core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.55},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: resto.healingPowerMultiplier(),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			// Wild Growth heals the druid and all party members within range.
			party := resto.Party
			if party == nil {
				spell.CalcAndDealHealing(sim, target, sim.Roll(wildGrowthLow, wildGrowthHigh), spell.OutcomeHealingCrit)
				return
			}
			for _, agent := range party.Players {
				unit := &agent.GetCharacter().Unit
				spell.CalcAndDealHealing(sim, unit, sim.Roll(wildGrowthLow, wildGrowthHigh), spell.OutcomeHealingCrit)
			}
		},
	})
}

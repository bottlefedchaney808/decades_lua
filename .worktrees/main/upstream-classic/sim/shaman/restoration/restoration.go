package restoration

import (
	"time"

	"github.com/wowsims/classic/sim/core"
	"github.com/wowsims/classic/sim/core/proto"
	"github.com/wowsims/classic/sim/shaman"
)

// Canonical Forever spell IDs for the level-60 restoration kit (verified
// against the Forever Wago SpellName cache).
const (
	spellIDHealingWave       = 331  // rank 1; higher ranks: 332/538/547/913/939/959/1354/10395/10396/11986
	spellIDLesserHealingWave = 8004
	spellIDChainHeal         = 1064
)

// 1.12-style base healing values. These are NOT verified Forever
// coefficients; they follow the existing flat-base-healing pattern used by
// the Healing Priest and Restoration Druid ports.
const (
	healingWaveBaseLow   = 589.0
	healingWaveBaseHigh  = 747.0
	lesserWaveBaseLow    = 266.0
	lesserWaveBaseHigh   = 342.0
	chainHealBaseLow     = 755.0
	chainHealBaseHigh    = 954.0
	// Chain heal bounces to additional party members at 40% of the primary hit.
	chainHealBouncePct = 0.40
)

func RegisterRestorationShaman() {
	core.RegisterAgentFactory(
		proto.Player_RestorationShaman{},
		proto.Spec_SpecRestorationShaman,
		func(character *core.Character, options *proto.Player) core.Agent {
			return NewRestorationShaman(character, options)
		},
		func(player *proto.Player, spec interface{}) {
			playerSpec, ok := spec.(*proto.Player_RestorationShaman)
			if !ok {
				panic("Invalid spec value for Restoration Shaman!")
			}
			player.Spec = playerSpec
		},
	)
}

func NewRestorationShaman(character *core.Character, options *proto.Player) *RestorationShaman {
	_ = options.GetRestorationShaman()

	resto := &RestorationShaman{
		Shaman: shaman.NewShaman(character, options.TalentsString),
	}

	return resto
}

type RestorationShaman struct {
	*shaman.Shaman
}

func (resto *RestorationShaman) GetShaman() *shaman.Shaman {
	return resto.Shaman
}

func (resto *RestorationShaman) Reset(sim *core.Simulation) {
	resto.Shaman.Reset(sim)
}

func (resto *RestorationShaman) Initialize() {
	// Base shaman registers lightning bolt, chain lightning, lightning
	// shield, all totems, imbues, etc. unconditionally.
	resto.Shaman.Initialize()
	resto.RegisterRestorationSpells()
}

func (resto *RestorationShaman) RegisterRestorationSpells() {
	resto.registerHealingWave()
	resto.registerLesserHealingWave()
	resto.registerChainHeal()
}

// healingMultiplier applies the restoration talents that increase direct
// healing: Improved Healing Wave (+5%/rank), Tidal Mastery (+15%/rank),
// Healing Way (+15%/rank).
func (resto *RestorationShaman) healingMultiplier() float64 {
	return 1 *
		(1 + .05*float64(resto.Talents.ImprovedHealingWave)) *
		(1 + .15*float64(resto.Talents.TidalMastery)) *
		(1 + .15*float64(resto.Talents.HealingWay))
}

func (resto *RestorationShaman) registerHealingWave() {
	resto.HealingWave = make([]*core.Spell, 2)
	resto.HealingWave[1] = resto.RegisterSpell(core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDHealingWave},
		SpellSchool: core.SpellSchoolNature,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType: core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.15, Multiplier: int32(100 - 5*resto.Talents.ImprovedHealingWave)},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: 1800 * time.Millisecond}},

		DamageMultiplier: resto.healingMultiplier(),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(healingWaveBaseLow, healingWaveBaseHigh)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)
		},
	})
}

func (resto *RestorationShaman) registerLesserHealingWave() {
	resto.LesserHealingWave = make([]*core.Spell, 2)
	resto.LesserHealingWave[1] = resto.RegisterSpell(core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDLesserHealingWave},
		SpellSchool: core.SpellSchoolNature,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType: core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.075},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: 1500 * time.Millisecond}},

		DamageMultiplier: resto.healingMultiplier(),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(lesserWaveBaseLow, lesserWaveBaseHigh)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)
		},
	})
}

func (resto *RestorationShaman) registerChainHeal() {
	resto.ChainHeal = make([]*core.Spell, 2)
	resto.ChainHeal[1] = resto.RegisterSpell(core.SpellConfig{
		ActionID:    core.ActionID{SpellID: spellIDChainHeal},
		SpellSchool: core.SpellSchoolNature,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       core.SpellFlagHelpful | core.SpellFlagAPL,
		DefenseType: core.DefenseTypeMagic,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.15},
		Cast:     core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: 1800 * time.Millisecond}},

		DamageMultiplier: resto.healingMultiplier(),
		ThreatMultiplier: 1,

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(chainHealBaseLow, chainHealBaseHigh)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)

			// Chain heal bounces to up to 2 additional party members at a
			// reduced percentage of the primary hit.
			party := resto.Env.Raid
			if party == nil {
				return
			}
			bounced := 0
			for _, unit := range party.AllPlayerUnits {
				if unit == target || bounced >= 2 {
					continue
				}
				spell.CalcAndDealHealing(sim, unit, baseHealing*chainHealBouncePct, spell.OutcomeHealing)
				bounced++
			}
		},
	})
}

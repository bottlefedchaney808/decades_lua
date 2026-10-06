package priest

import (
	"time"

	"github.com/wowsims/classic/sim/core"
)

func (priest *Priest) registerFlashHealSpell() {
	spellCoeff := 0.8057

	// Flash Heal rank 6 = 10917 (level 56); highest rank a level-60 priest has.
	priest.FlashHeal = make([]*core.Spell, 2)
	priest.FlashHeal[1] = priest.GetOrRegisterSpell(core.SpellConfig{
		SpellCode:   SpellCode_PriestFlashHeal,
		ActionID:    core.ActionID{SpellID: 10917},
		SpellSchool: core.SpellSchoolHoly,
		DefenseType: core.DefenseTypeMagic,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       SpellFlagPriest | core.SpellFlagHelpful | core.SpellFlagAPL,

		Rank:          1,
		RequiredLevel: 56,

		ManaCost: core.ManaCostOptions{BaseCost: 0.18},
		Cast: core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: time.Millisecond * 1500}},

		BonusCritRating:  float64(priest.Talents.HolySpecialization) * core.CritRatingPerCritChance,
		DamageMultiplier: 1 + .02*float64(priest.Talents.SpiritualHealing),
		ThreatMultiplier: 1 - []float64{0, .07, .14, .20}[priest.Talents.SilentResolve],

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(1896, 2203) + spellCoeff*spell.HealingPower(target)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)
		},
	})
}

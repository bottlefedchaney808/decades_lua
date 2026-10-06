package priest

import (
	"time"

	"github.com/wowsims/classic/sim/core"
)

func (priest *Priest) registerGreaterHealSpell() {
	spellCoeff := 1.6114

	// Greater Heal rank 7 = 25314 (level 60) — canonical id for this build.
	priest.GreaterHeal = make([]*core.Spell, 2)
	priest.GreaterHeal[1] = priest.GetOrRegisterSpell(core.SpellConfig{
		SpellCode:   SpellCode_PriestGreaterHeal,
		ActionID:    core.ActionID{SpellID: 25314},
		SpellSchool: core.SpellSchoolHoly,
		DefenseType: core.DefenseTypeMagic,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       SpellFlagPriest | core.SpellFlagHelpful | core.SpellFlagAPL,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.32, Multiplier: 100 - 5*int32(priest.Talents.ImprovedHealing)},
		Cast: core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: time.Second*3 - time.Millisecond*100*time.Duration(priest.Talents.DivineFury)}},

		BonusCritRating:  float64(priest.Talents.HolySpecialization) * core.CritRatingPerCritChance,
		DamageMultiplier: 1 + .02*float64(priest.Talents.SpiritualHealing),
		ThreatMultiplier: 1 - []float64{0, .07, .14, .20}[priest.Talents.SilentResolve],

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			baseHealing := sim.Roll(3980, 4621) + spellCoeff*spell.HealingPower(target)
			spell.CalcAndDealHealing(sim, target, baseHealing, spell.OutcomeHealingCrit)
		},
	})
}

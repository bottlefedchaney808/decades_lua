package priest

import (
	"time"

	"github.com/wowsims/classic/sim/core"
)

func (priest *Priest) registerPowerWordShieldSpell() {
	coeff := 0.8057
	wsDuration := time.Second * 15

	// Power Word: Shield rank 9 = 10901 (level 60) — canonical id for this build.
	priest.PowerWordShield = make([]*core.Spell, 2)
	priest.PowerWordShield[1] = priest.GetOrRegisterSpell(core.SpellConfig{
		ActionID:    core.ActionID{SpellID: 10901},
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       SpellFlagPriest | core.SpellFlagHelpful | core.SpellFlagAPL,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.23},
		Cast: core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},
		ExtraCastCondition: func(sim *core.Simulation, target *core.Unit) bool {
			return !priest.WeakenedSouls.Get(target).IsActive()
		},

		DamageMultiplier: 1 *
			(1 + .05*float64(priest.Talents.ImprovedPowerWordShield)) *
			(1 + .02*float64(priest.Talents.SpiritualHealing)),
		ThreatMultiplier: 1 - []float64{0, .07, .14, .20}[priest.Talents.SilentResolve],

		Shield: core.ShieldConfig{Aura: core.Aura{Label: "Power Word Shield", Duration: time.Second * 30}},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			shieldAmount := 2230.0 + coeff*spell.HealingPower(target)
			shield := spell.Shield(target)
			shield.Apply(sim, shieldAmount)
			weakenedSoul := priest.WeakenedSouls.Get(target)
			weakenedSoul.Duration = wsDuration
			weakenedSoul.Activate(sim)
		},
	})

	priest.WeakenedSouls = priest.NewRaidAuraArray(func(target *core.Unit) *core.Aura {
		return target.GetOrRegisterAura(core.Aura{
			Label:    "Weakened Soul",
			ActionID: core.ActionID{SpellID: 6788},
			Duration: time.Second * 15,
		})
	})
}

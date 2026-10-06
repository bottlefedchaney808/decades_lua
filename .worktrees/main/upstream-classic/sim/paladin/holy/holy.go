package holy

import (
	"github.com/wowsims/classic/sim/core"
	"github.com/wowsims/classic/sim/core/proto"
	"github.com/wowsims/classic/sim/paladin"
)

func RegisterHolyPaladin() {
	core.RegisterAgentFactory(
		proto.Player_HolyPaladin{},
		proto.Spec_SpecHolyPaladin,
		func(character *core.Character, options *proto.Player) core.Agent {
			return NewHolyPaladin(character, options)
		},
		func(player *proto.Player, spec interface{}) {
			playerSpec, ok := spec.(*proto.Player_HolyPaladin)
			if !ok {
				panic("Invalid spec value for Holy Paladin!")
			}
			player.Spec = playerSpec
		},
	)
}

func NewHolyPaladin(character *core.Character, options *proto.Player) *HolyPaladin {
	holyOptions := options.GetHolyPaladin().Options

	pal := paladin.NewPaladin(character, options, holyOptions)

	hp := &HolyPaladin{
		Paladin: pal,
	}

	hp.EnableAutoAttacks(hp, core.AutoAttackOptions{
		MainHand:       hp.WeaponFromMainHand(),
		AutoSwingMelee: true,
	})

	return hp
}

type HolyPaladin struct {
	*paladin.Paladin
}

func (hp *HolyPaladin) GetPaladin() *paladin.Paladin {
	return hp.Paladin
}

func (hp *HolyPaladin) Initialize() {
	hp.Paladin.Initialize()
}

func (hp *HolyPaladin) Reset(sim *core.Simulation) {
	hp.Paladin.Reset(sim)
}

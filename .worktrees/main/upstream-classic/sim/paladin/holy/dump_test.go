package holy_test

import (
	"fmt"
	"os"
	"testing"

	"github.com/wowsims/classic/sim"
	"github.com/wowsims/classic/sim/core"
	"github.com/wowsims/classic/sim/core/proto"
	"google.golang.org/protobuf/encoding/protojson"
)

func TestDumpHolySpells(t *testing.T) {
	sim.RegisterAll()
	raw, err := os.ReadFile(os.Getenv("LOCALAPPDATA") + "/Temp/forever_holy_default.json")
	if err != nil {
		t.Fatalf("read fixture: %v", err)
	}
	var simProto proto.RaidSimRequest
	if err := (protojson.UnmarshalOptions{DiscardUnknown: true}).Unmarshal(raw, &simProto); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	raid := core.NewRaid(simProto.Raid)
	agent := raid.Parties[0].Players[0]
	fmt.Printf("agent type: %T\n", agent)
	char := agent.GetCharacter()
	unit := &char.Unit
	fmt.Printf("=== %d spells in Spellbook (default Holy talents) ===\n", len(unit.Spellbook))
	for _, s := range unit.Spellbook {
		if s != nil {
			fmt.Printf("  spellID=%d spellCode=%d\n", s.SpellID, s.SpellCode)
		}
	}
}

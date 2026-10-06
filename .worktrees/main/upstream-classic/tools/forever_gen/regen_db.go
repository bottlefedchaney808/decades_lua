package main

import (
	"log"
	"os"

	"github.com/wowsims/classic/tools/database"
)

// Regenerate db.bin (and a canonical db.json) from the installed Forever db.json,
// validating the JSON against the proto schema via protojson round-trip.
func main() {
	in := "assets/database/db.json"
	binPath := "assets/database/db.bin"
	jsonPath := "assets/database/db.json"

	raw, err := os.ReadFile(in)
	if err != nil {
		log.Fatalf("read %s: %v", in, err)
	}
	db := database.ReadDatabaseFromJson(string(raw))
	log.Printf("Parsed Forever db: items=%d suffixes=%d enchants=%d",
		len(db.Items), len(db.RandomSuffixes), len(db.Enchants))

	db.WriteBinaryAndJson(binPath, jsonPath)
	log.Printf("Wrote %s and %s", binPath, jsonPath)

	bb, _ := os.Stat(binPath)
	jb, _ := os.Stat(jsonPath)
	log.Printf("db.bin=%d bytes  db.json=%d bytes", bb.Size(), jb.Size())
}

// Demo wizard: "Provision Acme CI" — a fake provisioning flow that exercises
// every runtime helper against stand-in endpoints, so it runs anywhere,
// offline, with zero accounts. In a generated wizard, this file is the only
// one the authoring agent writes.
package main

import (
	"fmt"
	goruntime "runtime"
)

func wizardDef() *Wizard {
	return &Wizard{
		Name:    "acme-ci",
		Title:   "Provision Acme CI",
		Intro:   "This demo walks you through wiring a (fictional) Acme project into CI: create the app, capture its credentials, pick the CI features, and push what CI needs to GitHub. Nothing here touches a real Acme — dashboard stops use example.com as a stand-in.",
		EnvFile: ".env.acme-demo",
		Steps: []Step{
			{
				Title: "Preflight",
				Run: func(c *Ctx) error {
					c.Say("First, confirm this machine has the tools the rest of the wizard leans on.")
					if err := c.Check("git is installed", "git --version"); err != nil {
						return err
					}
					if err := c.Check("Go toolchain answers", "go version"); err != nil {
						return err
					}
					c.Note("A real wizard checks whatever its later steps depend on: CLIs, auth, network.")
					return pause("Press Enter for the next step")
				},
			},
			{
				Title: "Create the Acme app",
				Run: func(c *Ctx) error {
					c.Say("Create the app in the Acme dashboard. The wizard opens the page; you click New App and pick a region.")
					c.OpenURL("https://example.com/")
					c.Note("(Stand-in for https://dashboard.acme.dev/apps/new — this is the demo.)")
					region, err := c.Select("ACME_REGION", "Which region did you pick?",
						"us-east", "eu-west", "ap-south")
					if err != nil {
						return err
					}
					name, err := c.Ask("ACME_APP_NAME", "What did you name the app?")
					if err != nil {
						return err
					}
					c.Say(fmt.Sprintf("Got it: %s in %s.", name, region))
					if err := c.WriteEnv("ACME_APP_NAME", name); err != nil {
						return err
					}
					return c.WriteEnv("ACME_REGION", region)
				},
			},
			{
				Title: "Capture credentials",
				Run: func(c *Ctx) error {
					c.Say("On the app's Settings → API page, Acme shows an App ID and a one-time API key.")
					c.Copy("Suggested key label", "acme-ci ("+c.st.Values["ACME_APP_NAME"]+")")
					c.Note("Paste that label into the 'key name' field so the key is findable later.")
					appID, err := c.Ask("ACME_APP_ID", "App ID (starts with app_)")
					if err != nil {
						return err
					}
					apiKey, err := c.AskSecret("ACME_API_KEY", "API key (hidden as you type)")
					if err != nil {
						return err
					}
					if err := c.WriteEnv("ACME_APP_ID", appID); err != nil {
						return err
					}
					return c.WriteEnv("ACME_API_KEY", apiKey)
				},
			},
			{
				Title: "Choose CI features",
				Run: func(c *Ctx) error {
					features, err := c.MultiSelect("ACME_CI_FEATURES", "Which CI features should Acme run?",
						"Preview deploys", "Test sharding", "Nightly smoke run", "Release tagging")
					if err != nil {
						return err
					}
					if len(features) == 0 {
						c.Warn("No features picked — CI will only build.")
					}
					return c.WriteEnv("ACME_CI_FEATURES", c.st.Values["ACME_CI_FEATURES"])
				},
			},
			{
				Title: "Push to GitHub Actions",
				Run: func(c *Ctx) error {
					c.Say("CI needs the API key as a repository secret and the region as a variable.")
					ok, err := c.Confirm("Push ACME_API_KEY and ACME_REGION to this repo's GitHub Actions?")
					if err != nil {
						return err
					}
					if !ok {
						c.Note("Skipped — the finish screen lists what to set by hand.")
						c.st.Skipped = appendUnique(c.st.Skipped, "GitHub secret ACME_API_KEY — declined; set it by hand")
						c.st.Skipped = appendUnique(c.st.Skipped, "GitHub variable ACME_REGION — declined; set it by hand")
						return nil
					}
					c.SetSecret("ACME_API_KEY", readEnvValue(c.envFile, "ACME_API_KEY"))
					c.SetVar("ACME_REGION", c.st.Values["ACME_REGION"])
					return pause("Press Enter for the final step")
				},
			},
			{
				Title: "Verify the wiring",
				Run: func(c *Ctx) error {
					c.Say("Last: prove the captured config is really on disk.")
					// Shell built-ins differ per OS; branch when a command isn't portable.
					probe := "grep -c ACME_ " + c.envFile
					if goruntime.GOOS == "windows" {
						probe = "findstr ACME_ " + c.envFile
					}
					if err := c.Check("Env file holds the ACME_ values", probe); err != nil {
						return err
					}
					c.Note("A real wizard verifies against the live service: call the API with the new key, or trigger a CI dry run.")
					return nil
				},
			},
		},
	}
}

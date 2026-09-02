// crank-wizard runtime — the immutable half of a generated wizard.
// Authored steps live in steps.go; this file is byte-identical in every
// wizard the crank-wizard skill generates. Never hand-edit it.
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	goruntime "runtime"
	"strconv"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/huh"
	"github.com/charmbracelet/lipgloss"
)

// ---------- authoring surface ----------

// Step is one screen of the wizard. Run does the step's work through the
// Ctx helpers and returns nil when the step is complete.
type Step struct {
	Title string
	Run   func(*Ctx) error
}

// Wizard is the definition steps.go provides via wizardDef().
type Wizard struct {
	Name    string // kebab-case id; scopes the state file
	Title   string
	Intro   string
	EnvFile string // optional; defaults to ".env"
	Steps   []Step
}

// Ctx is the API a step's Run function talks to.
type Ctx struct {
	w        *Wizard
	st       *state
	envFile  string
	doN      int // Do lines numbered so far on the current step
	ghTested bool
	ghOK     bool
}

// ---------- theme ----------

var (
	colPrimary = lipgloss.AdaptiveColor{Light: "#5A56E0", Dark: "#7D79F6"}
	colAccent  = lipgloss.AdaptiveColor{Light: "#D5008F", Dark: "#FF6AC1"}
	colOK      = lipgloss.AdaptiveColor{Light: "#0E8A6D", Dark: "#2EE6A8"}
	colWarn    = lipgloss.AdaptiveColor{Light: "#A87900", Dark: "#F5C518"}
	colDim     = lipgloss.AdaptiveColor{Light: "#8A8A94", Dark: "#6C6C76"}

	styleTitle  = lipgloss.NewStyle().Bold(true).Foreground(colPrimary)
	styleStage  = lipgloss.NewStyle().Bold(true).Foreground(colAccent)
	styleDim    = lipgloss.NewStyle().Foreground(colDim)
	styleWarn   = lipgloss.NewStyle().Foreground(colWarn)
	styleOK     = lipgloss.NewStyle().Foreground(colOK)
	styleBanner = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colPrimary).
			Padding(1, 3)
)

var errAborted = errors.New("aborted by user")

func theme() *huh.Theme { return huh.ThemeCharm() }

// ---------- entry point ----------

func main() {
	listFlag := flag.Bool("list", false, "print the step plan and exit")
	freshFlag := flag.Bool("fresh", false, "discard saved progress and start over")
	envFlag := flag.String("env", "", "override the env file path")
	flag.Parse()

	w := wizardDef()
	if err := run(w, *listFlag, *freshFlag, *envFlag); err != nil {
		if errors.Is(err, errAborted) || errors.Is(err, huh.ErrUserAborted) {
			fmt.Println()
			fmt.Println(styleDim.Render("Paused. Progress is saved — rerun to resume."))
			os.Exit(130)
		}
		fmt.Println()
		fmt.Println(styleWarn.Render("✗ " + err.Error()))
		fmt.Println(styleDim.Render("Progress is saved — rerun to resume from this step."))
		os.Exit(1)
	}
}

func run(w *Wizard, list, fresh bool, envOverride string) error {
	envFile := ".env"
	if w.EnvFile != "" {
		envFile = w.EnvFile
	}
	if envOverride != "" {
		envFile = envOverride
	}

	if list {
		fmt.Println(styleTitle.Render(w.Title))
		fmt.Println(styleDim.Render(fmt.Sprintf("%d steps · values land in %s", len(w.Steps), envFile)))
		for i, s := range w.Steps {
			fmt.Printf("  %d. %s\n", i+1, s.Title)
		}
		return nil
	}

	root, err := chdirRepoRoot()
	if err != nil {
		return err
	}

	st := loadState(w.Name)
	if fresh {
		st = newState()
	}
	c := &Ctx{w: w, st: st, envFile: envFile}

	clearScreen()
	banner := styleTitle.Render("✦ "+w.Title) + "\n" +
		styleDim.Render(fmt.Sprintf("%d steps · values land in %s", len(w.Steps), envFile))
	fmt.Println(styleBanner.Render(banner))
	fmt.Println(styleDim.Render("Working in " + root))
	if w.Intro != "" {
		fmt.Println(wrap(w.Intro))
	}
	fmt.Println(styleDim.Render("Ctrl-C any time — progress is saved; rerun to resume."))
	fmt.Println()

	start := 0
	if st.Completed > 0 && st.Completed < len(w.Steps) {
		resume := true
		err := form(huh.NewConfirm().
			Title(fmt.Sprintf("Found saved progress — resume from step %d, %q?", st.Completed+1, w.Steps[st.Completed].Title)).
			Affirmative("Resume").Negative("Start over").
			Value(&resume))
		if err != nil {
			return err
		}
		if resume {
			start = st.Completed
		} else {
			*st = *newState()
			c.saveState()
		}
	} else {
		if err := pause("Press Enter to begin"); err != nil {
			return err
		}
	}

	for i := start; i < len(w.Steps); i++ {
		step := w.Steps[i]
		clearScreen()
		fmt.Println(styleStage.Render(fmt.Sprintf("▸ Step %d/%d · %s", i+1, len(w.Steps), step.Title)))
		fmt.Println(progressDots(i, len(w.Steps)))
		fmt.Println()
		c.doN = 0
		if err := step.Run(c); err != nil {
			c.saveState()
			return err
		}
		st.Completed = i + 1
		c.saveState()
	}

	c.finish()
	return nil
}

// ---------- step-flow chrome ----------

// chdirRepoRoot moves to the nearest ancestor holding a .git entry and returns
// it, so Check commands, the env file, and saved progress all land at the repo
// root however the wizard was launched (`go -C wizards/<name> run .` from the
// root, or `go run .` from inside the wizard's directory). Outside any
// checkout it stays where it started.
func chdirRepoRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}
	for probe := dir; ; probe = filepath.Dir(probe) {
		if _, err := os.Stat(filepath.Join(probe, ".git")); err == nil {
			return probe, os.Chdir(probe)
		}
		if filepath.Dir(probe) == probe {
			return dir, nil
		}
	}
}

func clearScreen() { fmt.Print("\033[2J\033[H") }

func progressDots(current, total int) string {
	var b strings.Builder
	for i := 0; i < total; i++ {
		switch {
		case i < current:
			b.WriteString(styleOK.Render("●"))
		case i == current:
			b.WriteString(styleStage.Render("●"))
		default:
			b.WriteString(styleDim.Render("○"))
		}
		b.WriteString(" ")
	}
	return b.String()
}

func wrap(s string) string {
	return lipgloss.NewStyle().Width(76).Render(s)
}

func pause(msg string) error {
	fmt.Print(styleDim.Render(msg + " "))
	_, err := bufio.NewReader(os.Stdin).ReadString('\n')
	fmt.Println()
	if err != nil {
		return errAborted
	}
	return nil
}

func form(field huh.Field) error {
	return huh.NewForm(huh.NewGroup(field)).WithTheme(theme()).Run()
}

func (c *Ctx) finish() {
	clearScreen()
	cheer := styleStage.Render("✦ ✦ ✦") + styleTitle.Render("  All done!  ") + styleStage.Render("✦ ✦ ✦")
	fmt.Println(styleBanner.Render(cheer))
	fmt.Println(styleOK.Render(fmt.Sprintf("✓ %d steps completed", len(c.w.Steps))))
	if n := len(c.st.WroteEnv); n > 0 {
		fmt.Println(styleOK.Render(fmt.Sprintf("✓ %d value(s) written to %s", n, c.envFile)) +
			styleDim.Render("  ("+strings.Join(c.st.WroteEnv, ", ")+")"))
	}
	if n := len(c.st.SetSecrets); n > 0 {
		fmt.Println(styleOK.Render(fmt.Sprintf("✓ %d GitHub secret(s)/variable(s) set", n)) +
			styleDim.Render("  ("+strings.Join(c.st.SetSecrets, ", ")+")"))
	}
	if len(c.st.Skipped) > 0 {
		fmt.Println(styleWarn.Render("⚠ Still to do by hand:"))
		for _, s := range c.st.Skipped {
			fmt.Println("  • " + s)
		}
	}
	fmt.Println()
	clearState(c.w.Name)
}

// ---------- state (progress + non-secret values; secrets never land here) ----------

type state struct {
	Completed  int               `json:"completed"`
	Values     map[string]string `json:"values"`
	WroteEnv   []string          `json:"wroteEnv"`
	SetSecrets []string          `json:"setSecrets"`
	Skipped    []string          `json:"skipped"`
}

func newState() *state { return &state{Values: map[string]string{}} }

func statePath(name string) string { return ".wizard-state." + name + ".json" }

func loadState(name string) *state {
	st := newState()
	data, err := os.ReadFile(statePath(name))
	if err != nil {
		return st
	}
	if json.Unmarshal(data, st) != nil {
		return newState()
	}
	if st.Values == nil {
		st.Values = map[string]string{}
	}
	return st
}

func (c *Ctx) saveState() {
	data, err := json.MarshalIndent(c.st, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(statePath(c.w.Name), data, 0o600)
}

func clearState(name string) { _ = os.Remove(statePath(name)) }

func appendUnique(list []string, v string) []string {
	for _, x := range list {
		if x == v {
			return list
		}
	}
	return append(list, v)
}

// ---------- output helpers ----------

// Say prints a plain line of guidance.
func (c *Ctx) Say(s string) { fmt.Println(wrap(s)) }

// Note prints a dim aside.
func (c *Ctx) Note(s string) { fmt.Println(styleDim.Render(wrap(s))) }

// Warn prints a yellow caution line.
func (c *Ctx) Warn(s string) { fmt.Println(styleWarn.Render("⚠ " + s)) }

// Do prints one action the human takes, numbered from 1 on each step and in
// the step's accent color, so the clicks are the brightest lines on screen.
func (c *Ctx) Do(s string) {
	c.doN++
	fmt.Println(styleStage.Render(fmt.Sprintf("  %d. ", c.doN)) + wrap(s))
}

// OpenURL opens url in the default browser (macOS/Windows) and says so.
// When opening fails, it tells the human to open the URL themselves.
func (c *Ctx) OpenURL(url string) {
	fmt.Println(styleTitle.Render("‣ ") + "Opening " + styleTitle.Render(url))
	var cmd *exec.Cmd
	switch goruntime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	if err := cmd.Start(); err != nil {
		c.Note("Could not open a browser here — open the URL above yourself.")
	}
}

// Copy puts text on the system clipboard, says what landed there, and waits
// for Enter before returning: the clipboard holds one value, so the next Copy
// only runs once this one has been pasted.
func (c *Ctx) Copy(label, text string) error {
	var cmd *exec.Cmd
	switch goruntime.GOOS {
	case "windows":
		cmd = exec.Command("clip")
	case "darwin":
		cmd = exec.Command("pbcopy")
	default:
		cmd = exec.Command("xclip", "-selection", "clipboard")
	}
	cmd.Stdin = strings.NewReader(text)
	if err := cmd.Run(); err != nil {
		c.Note(fmt.Sprintf("Clipboard unavailable — copy this yourself: %s", text))
	} else {
		fmt.Println(styleOK.Render("✓ ") + label + styleDim.Render(" — copied to clipboard"))
	}
	return pause("Press Enter once you've pasted it")
}

// ---------- input helpers ----------

// Ask captures a visible value. A value already in the env file or saved
// state is prefilled so Enter keeps it. The result is remembered for resume.
func (c *Ctx) Ask(key, prompt string) (string, error) {
	current := c.st.Values[key]
	if current == "" {
		current = readEnvValue(c.envFile, key)
	}
	val := current
	input := huh.NewInput().Title(prompt).Value(&val)
	if current != "" {
		input = input.Description("Enter keeps the current value")
	}
	if err := form(input); err != nil {
		return "", err
	}
	val = strings.TrimSpace(val)
	c.st.Values[key] = val
	c.saveState()
	return val, nil
}

// AskSecret captures a hidden value. It is never written to the state file;
// an empty entry keeps a value already present in the env file.
func (c *Ctx) AskSecret(key, prompt string) (string, error) {
	existing := readEnvValue(c.envFile, key)
	var val string
	input := huh.NewInput().Title(prompt).EchoMode(huh.EchoModePassword).Value(&val)
	if existing != "" {
		input = input.Description("A value exists in " + c.envFile + " — Enter keeps it")
	}
	if err := form(input); err != nil {
		return "", err
	}
	val = strings.TrimSpace(val)
	if val == "" && existing != "" {
		c.Note("Kept the existing value.")
		return existing, nil
	}
	return val, nil
}

// Select captures one choice from options. The pick is remembered for resume.
func (c *Ctx) Select(key, prompt string, options ...string) (string, error) {
	val := c.st.Values[key]
	sel := huh.NewSelect[string]().Title(prompt).Options(huh.NewOptions(options...)...).Value(&val)
	if err := form(sel); err != nil {
		return "", err
	}
	c.st.Values[key] = val
	c.saveState()
	return val, nil
}

// MultiSelect captures any number of choices from options.
func (c *Ctx) MultiSelect(key, prompt string, options ...string) ([]string, error) {
	var vals []string
	if saved := c.st.Values[key]; saved != "" {
		vals = strings.Split(saved, ",")
	}
	sel := huh.NewMultiSelect[string]().Title(prompt).Options(huh.NewOptions(options...)...).Value(&vals)
	if err := form(sel); err != nil {
		return nil, err
	}
	c.st.Values[key] = strings.Join(vals, ",")
	c.saveState()
	return vals, nil
}

// Confirm gates an irreversible action on an explicit yes.
func (c *Ctx) Confirm(question string) (bool, error) {
	var ok bool
	err := form(huh.NewConfirm().Title(question).Affirmative("Yes").Negative("No").Value(&ok))
	return ok, err
}

// ---------- automated checks ----------

type checkDoneMsg struct {
	out string
	err error
}

type checkModel struct {
	sp     spinner.Model
	label  string
	start  time.Time
	out    string
	err    error
	done   bool
	cancel context.CancelFunc
}

func (m checkModel) Init() tea.Cmd { return m.sp.Tick }

func (m checkModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case checkDoneMsg:
		m.done, m.out, m.err = true, msg.out, msg.err
		return m, tea.Quit
	case tea.KeyMsg:
		if msg.String() == "ctrl+c" {
			m.cancel()
			m.done, m.err = true, errAborted
			return m, tea.Quit
		}
	case spinner.TickMsg:
		var cmd tea.Cmd
		m.sp, cmd = m.sp.Update(msg)
		return m, cmd
	}
	return m, nil
}

func (m checkModel) View() string {
	if m.done {
		return ""
	}
	return fmt.Sprintf("%s %s %s", m.sp.View(), m.label,
		styleDim.Render(fmt.Sprintf("(%ds)", int(time.Since(m.start).Seconds()))))
}

// Check runs command behind a spinner and gates the step on it passing.
// It runs the moment it is reached: when the human must act first, pause
// before it with the done condition named ("Press Enter once the rule is
// deployed"). On failure the human chooses retry, skip (logged for the finish
// screen's hand-finish list), or abort.
func (c *Ctx) Check(label, command string) error {
	for {
		ctx, cancel := context.WithCancel(context.Background())
		m := checkModel{
			sp:     spinner.New(spinner.WithSpinner(spinner.Dot), spinner.WithStyle(styleStage)),
			label:  label,
			start:  time.Now(),
			cancel: cancel,
		}
		p := tea.NewProgram(m)
		go func() {
			out, err := runShell(ctx, command)
			p.Send(checkDoneMsg{out: out, err: err})
		}()
		final, err := p.Run()
		cancel()
		if err != nil {
			return err
		}
		res := final.(checkModel)
		if errors.Is(res.err, errAborted) {
			return errAborted
		}
		if res.err == nil {
			fmt.Println(styleOK.Render("✓ ") + label)
			return nil
		}

		fmt.Println(styleWarn.Render("✗ " + label))
		if tail := outputTail(res.out, 15); tail != "" {
			fmt.Println(styleDim.Render(tail))
		}
		choice := "Retry"
		sel := huh.NewSelect[string]().
			Title("The check failed — what now?").
			Options(huh.NewOptions("Retry", "Skip and finish by hand", "Abort")...).
			Value(&choice)
		if err := form(sel); err != nil {
			return err
		}
		switch choice {
		case "Retry":
			continue
		case "Skip and finish by hand":
			c.st.Skipped = appendUnique(c.st.Skipped, label+" — check failed; verify by hand")
			c.saveState()
			return nil
		default:
			return errAborted
		}
	}
}

func runShell(ctx context.Context, command string) (string, error) {
	var cmd *exec.Cmd
	if goruntime.GOOS == "windows" {
		cmd = exec.CommandContext(ctx, "cmd", "/C", command)
	} else {
		cmd = exec.CommandContext(ctx, "sh", "-c", command)
	}
	out, err := cmd.CombinedOutput()
	return string(out), err
}

func outputTail(out string, n int) string {
	lines := strings.Split(strings.TrimRight(out, "\n"), "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return strings.TrimSpace(strings.Join(lines, "\n"))
}

// ---------- persistence helpers ----------

// WriteEnv upserts KEY=VALUE into the env file and says so.
func (c *Ctx) WriteEnv(key, value string) error {
	if err := upsertEnv(c.envFile, key, value); err != nil {
		return fmt.Errorf("writing %s to %s: %w", key, c.envFile, err)
	}
	c.st.WroteEnv = appendUnique(c.st.WroteEnv, key)
	c.saveState()
	fmt.Println(styleOK.Render("✓ ") + key + styleDim.Render(" → "+c.envFile))
	return nil
}

// SetSecret pushes a GitHub Actions secret via gh. When gh is missing or
// unauthenticated the push is skipped and logged for the finish screen.
func (c *Ctx) SetSecret(name, value string) {
	c.ghPush("secret", name, value)
}

// SetVar pushes a GitHub Actions variable via gh, with the same graceful skip.
func (c *Ctx) SetVar(name, value string) {
	c.ghPush("variable", name, value)
}

func (c *Ctx) ghPush(kind, name, value string) {
	if !c.ghReady() {
		c.st.Skipped = appendUnique(c.st.Skipped,
			fmt.Sprintf("GitHub %s %s — gh unavailable; set it by hand", kind, name))
		c.saveState()
		c.Warn(fmt.Sprintf("gh unavailable — GitHub %s %s goes on the hand-finish list.", kind, name))
		return
	}
	cmd := exec.Command("gh", kind, "set", name, "--body", value)
	if out, err := cmd.CombinedOutput(); err != nil {
		c.st.Skipped = appendUnique(c.st.Skipped,
			fmt.Sprintf("GitHub %s %s — push failed; set it by hand", kind, name))
		c.saveState()
		c.Warn(fmt.Sprintf("Could not set GitHub %s %s: %s", kind, name, outputTail(string(out), 3)))
		return
	}
	c.st.SetSecrets = appendUnique(c.st.SetSecrets, name)
	c.saveState()
	fmt.Println(styleOK.Render("✓ ") + name + styleDim.Render(" → GitHub "+kind))
}

func (c *Ctx) ghReady() bool {
	if c.ghTested {
		return c.ghOK
	}
	c.ghTested = true
	if _, err := exec.LookPath("gh"); err != nil {
		return false
	}
	c.ghOK = exec.Command("gh", "auth", "status").Run() == nil
	return c.ghOK
}

// ---------- env file ----------

func readEnvValue(path, key string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, key+"=") {
			continue
		}
		val := strings.TrimPrefix(line, key+"=")
		if unq, err := strconv.Unquote(val); err == nil {
			return unq
		}
		return val
	}
	return ""
}

func upsertEnv(path, key, value string) error {
	if strings.ContainsAny(value, " \t\"'#") {
		value = strconv.Quote(value)
	}
	entry := key + "=" + value
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return os.WriteFile(path, []byte(entry+"\n"), 0o600)
	}
	if err != nil {
		return err
	}
	lines := strings.Split(strings.TrimRight(string(data), "\n"), "\n")
	replaced := false
	for i, line := range lines {
		if strings.HasPrefix(strings.TrimSpace(line), key+"=") {
			lines[i] = entry
			replaced = true
		}
	}
	if !replaced {
		lines = append(lines, entry)
	}
	return os.WriteFile(path, []byte(strings.Join(lines, "\n")+"\n"), 0o600)
}

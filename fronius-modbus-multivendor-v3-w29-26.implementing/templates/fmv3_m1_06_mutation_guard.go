package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/constant"
	"go/format"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
)

type mutationContract struct {
	target symbolIdentity
	before string
	after  string
}

var caseContracts = map[string]mutationContract{
	"M1-06-DELIVERABILITY-EXCLUSIONS":       {symbolIdentity{"NewRuntimeAcquisition", "function", ""}, "return &OpaqueRuntimeCapability{}", "return nil"},
	"M1-06-COPY-ONE-WINNER":                 {symbolIdentity{"Claim", "method", "*OpaqueRuntimeCapability"}, "return true", "return false"},
	"M1-06-STALE-INSTANCE-CANCEL-ISOLATION": {symbolIdentity{"CancelOpen", "method", "*AttemptInstance"}, "return true", "return false"},
	"M1-06-TERMINAL-OUTCOMES":               {symbolIdentity{"IsTerminal", "method", "TerminalOutcome"}, "return true", "return false"},
	"M1-06-MEMBERSHIP-CLOSE-RACE":           {symbolIdentity{"CloseMembership", "method", "*AttemptInstance"}, "return true", "return false"},
	"M1-06-BOUNDS-OVERFLOW":                 {symbolIdentity{"NewBoundedCapability", "function", ""}, "return &OpaqueRuntimeCapability{}", "return nil"},
	"M1-06-SEQUENCE-EXHAUSTION":             {symbolIdentity{"ReserveTerminalSequence", "function", ""}, "return 1", "return 0"},
	"M1-06-COALESCED-ISOLATION":             {symbolIdentity{"NewRuntimeAcquisition", "function", ""}, "return &OpaqueRuntimeCapability{}", "return nil"},
}

var conformanceCalls = map[string]struct {
	testFunction string
	required     []string
}{
	"M1-06-DELIVERABILITY-EXCLUSIONS":       {"TestDeliverabilityExclusions", []string{"NewRuntimeAcquisition"}},
	"M1-06-COPY-ONE-WINNER":                 {"TestCopiedCapabilityOneWinner", []string{"Claim"}},
	"M1-06-STALE-INSTANCE-CANCEL-ISOLATION": {"TestStaleAttemptInstanceCancellationIsolation", []string{"CancelOpen"}},
	"M1-06-TERMINAL-OUTCOMES":               {"TestTerminalOutcomes", []string{"TerminalOutcome", "IsTerminal"}},
	"M1-06-MEMBERSHIP-CLOSE-RACE":           {"TestAttemptMembershipCloseRegistrationRace", []string{"CloseMembership"}},
	"M1-06-BOUNDS-OVERFLOW":                 {"TestBoundsAndOverflow", []string{"NewBoundedCapability"}},
	"M1-06-SEQUENCE-EXHAUSTION":             {"TestTerminalSequenceExhaustion", []string{"ReserveTerminalSequence"}},
	"M1-06-COALESCED-ISOLATION":             {"TestCoalescedDependentIsolation", []string{"NewRuntimeAcquisition"}},
}

type symbolIdentity struct {
	Name     string
	Kind     string
	Receiver string
}

func (identity symbolIdentity) key() string {
	return identity.Kind + "\x00" + identity.Receiver + "\x00" + identity.Name
}

type symbolDescriptor struct {
	Name      string `json:"name"`
	Kind      string `json:"kind"`
	Receiver  string `json:"receiver"`
	Signature string `json:"signature"`
}

func (descriptor symbolDescriptor) identity() symbolIdentity {
	return symbolIdentity{descriptor.Name, descriptor.Kind, descriptor.Receiver}
}

var fixedProductionSymbols = []symbolIdentity{
	{"OpaqueRuntimeCapability", "type", ""},
	{"AttemptInstance", "type", ""},
	{"TerminalOutcome", "type", ""},
	{"NewRuntimeAcquisition", "function", ""},
	{"Claim", "method", "*OpaqueRuntimeCapability"},
	{"CloseMembership", "method", "*AttemptInstance"},
	{"CancelOpen", "method", "*AttemptInstance"},
	{"NewBoundedCapability", "function", ""},
	{"ReserveTerminalSequence", "function", ""},
	{"IsTerminal", "method", "TerminalOutcome"},
}

var fixedProductionByName = func() map[string]symbolIdentity {
	result := map[string]symbolIdentity{}
	for _, symbol := range fixedProductionSymbols {
		result[symbol.Name] = symbol
	}
	return result
}()

type reportGoList struct {
	PackageDir         string   `json:"package_dir"`
	PackageQuery       string   `json:"package_query"`
	PackageName        string   `json:"package_name"`
	ImportPath         string   `json:"import_path"`
	GOOS               string   `json:"goos"`
	GOARCH             string   `json:"goarch"`
	CGOEnabled         string   `json:"cgo_enabled"`
	GOWORK             string   `json:"gowork"`
	GoFiles            []string `json:"go_files"`
	CompiledGoFiles    []string `json:"compiled_go_files"`
	TestGoFiles        []string `json:"test_go_files"`
	IgnoredGoFiles     []string `json:"ignored_go_files"`
	CgoFiles           []string `json:"cgo_files"`
	CFiles             []string `json:"c_files"`
	CXXFiles           []string `json:"cxx_files"`
	MFiles             []string `json:"m_files"`
	HFiles             []string `json:"h_files"`
	FFiles             []string `json:"f_files"`
	SFiles             []string `json:"s_files"`
	SwigFiles          []string `json:"swig_files"`
	SwigCXXFiles       []string `json:"swig_cxx_files"`
	SysoFiles          []string `json:"syso_files"`
	XTestGoFiles       []string `json:"x_test_go_files"`
	IgnoredOtherFiles  []string `json:"ignored_other_files"`
	EmbedPatterns      []string `json:"embed_patterns"`
	EmbedFiles         []string `json:"embed_files"`
	TestEmbedPatterns  []string `json:"test_embed_patterns"`
	TestEmbedFiles     []string `json:"test_embed_files"`
	XTestEmbedPatterns []string `json:"x_test_embed_patterns"`
	XTestEmbedFiles    []string `json:"x_test_embed_files"`
}

type conformanceReport struct {
	GoList     reportGoList `json:"go_list"`
	Production []struct {
		Path    string             `json:"path"`
		Symbols []symbolDescriptor `json:"symbols"`
	} `json:"production"`
	Cases []struct {
		CaseID       string `json:"case_id"`
		TestFunction string `json:"test_function"`
	} `json:"cases"`
}

type goListResult struct {
	Dir                string
	ImportPath         string
	Name               string
	GoFiles            []string
	CompiledGoFiles    []string
	TestGoFiles        []string
	IgnoredGoFiles     []string
	CgoFiles           []string
	CFiles             []string
	CXXFiles           []string
	MFiles             []string
	HFiles             []string
	FFiles             []string
	SFiles             []string
	SwigFiles          []string
	SwigCXXFiles       []string
	SysoFiles          []string
	XTestGoFiles       []string
	IgnoredOtherFiles  []string
	EmbedPatterns      []string
	EmbedFiles         []string
	TestEmbedPatterns  []string
	TestEmbedFiles     []string
	XTestEmbedPatterns []string
	XTestEmbedFiles    []string
}

func git(args ...string) ([]byte, error) {
	command := exec.Command("/usr/bin/git", append([]string{"--no-replace-objects"}, args...)...)
	env := make([]string, 0, len(os.Environ())+1)
	for _, entry := range os.Environ() {
		if !strings.HasPrefix(entry, "GIT_") {
			env = append(env, entry)
		}
	}
	command.Env = append(env,
		"GIT_NO_REPLACE_OBJECTS=1",
		"GIT_CONFIG_NOSYSTEM=1",
		"GIT_CONFIG_GLOBAL=/dev/null",
	)
	return command.Output()
}

func source(revision, path string) ([]byte, error) {
	return git("show", revision+":"+path)
}

func receiverName(fileSet *token.FileSet, function *ast.FuncDecl) (string, error) {
	if function.Recv == nil || len(function.Recv.List) != 1 {
		return "", nil
	}
	var rendered bytes.Buffer
	if err := format.Node(&rendered, fileSet, function.Recv.List[0].Type); err != nil {
		return "", err
	}
	return rendered.String(), nil
}

func declarations(path string, data []byte) (map[string]string, error) {
	fileSet := token.NewFileSet()
	file, err := parser.ParseFile(fileSet, path, data, 0)
	if err != nil {
		return nil, err
	}
	result := map[string]string{}
	for declarationIndex, declaration := range file.Decls {
		switch value := declaration.(type) {
		case *ast.FuncDecl:
			receiver, receiverErr := receiverName(fileSet, value)
			if receiverErr != nil {
				return nil, receiverErr
			}
			kind := "function"
			if value.Recv != nil {
				kind = "method"
			}
			identity := symbolIdentity{value.Name.Name, kind, receiver}
			var rendered bytes.Buffer
			if err := format.Node(&rendered, fileSet, declaration); err != nil {
				return nil, err
			}
			if _, exists := result[identity.key()]; exists {
				return nil, fmt.Errorf("duplicate declaration %s", value.Name.Name)
			}
			result[identity.key()] = rendered.String()
		case *ast.GenDecl:
			for specificationIndex, specification := range value.Specs {
				if typed, ok := specification.(*ast.TypeSpec); ok {
					var rendered bytes.Buffer
					if err := format.Node(&rendered, fileSet, typed); err != nil {
						return nil, err
					}
					identity := symbolIdentity{typed.Name.Name, "type", ""}
					if _, exists := result[identity.key()]; exists {
						return nil, fmt.Errorf("duplicate declaration %s", typed.Name.Name)
					}
					result[identity.key()] = rendered.String()
					continue
				}
				var rendered bytes.Buffer
				if err := format.Node(&rendered, fileSet, specification); err != nil {
					return nil, err
				}
				result[fmt.Sprintf("@decl-%d-spec-%d", declarationIndex, specificationIndex)] = rendered.String()
			}
		}
	}
	return result, nil
}

func declarationSpan(path string, data []byte, target symbolIdentity) (int, int, error) {
	fileSet := token.NewFileSet()
	file, err := parser.ParseFile(fileSet, path, data, parser.ParseComments)
	if err != nil {
		return 0, 0, err
	}
	start, end := -1, -1
	for _, declaration := range file.Decls {
		function, ok := declaration.(*ast.FuncDecl)
		if !ok {
			continue
		}
		receiver, receiverErr := receiverName(fileSet, function)
		if receiverErr != nil {
			return 0, 0, receiverErr
		}
		kind := "function"
		if function.Recv != nil {
			kind = "method"
		}
		if (symbolIdentity{function.Name.Name, kind, receiver}) != target {
			continue
		}
		if start != -1 {
			return 0, 0, fmt.Errorf("duplicate target declaration %s", target.Name)
		}
		start = fileSet.PositionFor(function.Pos(), false).Offset
		end = fileSet.PositionFor(function.End(), false).Offset
	}
	if start < 0 || end <= start || end > len(data) {
		return 0, 0, fmt.Errorf("target declaration %s is absent or invalid", target.Name)
	}
	return start, end, nil
}

func typeString(value types.Type) string {
	return types.TypeString(value, func(*types.Package) string { return "" })
}

func objectDescriptor(object types.Object) (symbolDescriptor, bool) {
	switch typed := object.(type) {
	case *types.TypeName:
		return symbolDescriptor{
			Name: typed.Name(), Kind: "type", Signature: typeString(typed.Type()),
		}, true
	case *types.Func:
		signature, ok := typed.Type().(*types.Signature)
		if !ok {
			return symbolDescriptor{}, false
		}
		kind := "function"
		receiver := ""
		if signature.Recv() != nil {
			kind = "method"
			receiver = typeString(signature.Recv().Type())
		}
		return symbolDescriptor{
			Name: typed.Name(), Kind: kind, Receiver: receiver,
			Signature: typeString(signature),
		}, true
	default:
		return symbolDescriptor{}, false
	}
}

func callObject(call *ast.CallExpr, info *types.Info) types.Object {
	switch function := call.Fun.(type) {
	case *ast.Ident:
		return info.Uses[function]
	case *ast.SelectorExpr:
		if selection := info.Selections[function]; selection != nil {
			return selection.Obj()
		}
		return info.Uses[function.Sel]
	default:
		return nil
	}
}

func constantBool(expression ast.Expr, info *types.Info) (bool, bool) {
	value := info.Types[expression].Value
	if value == nil || value.Kind() != constant.Bool {
		return false, false
	}
	return constant.BoolVal(value), true
}

func constantFalse(expression ast.Expr, info *types.Info) bool {
	value, ok := constantBool(expression, info)
	return ok && !value
}

func conditionHasMaskingConstant(expression ast.Expr, info *types.Info) bool {
	binary, ok := expression.(*ast.BinaryExpr)
	if !ok {
		return false
	}
	left, leftConstant := constantBool(binary.X, info)
	right, rightConstant := constantBool(binary.Y, info)
	if binary.Op == token.LAND && ((leftConstant && !left) || (rightConstant && !right)) {
		return true
	}
	if binary.Op == token.LOR && ((leftConstant && left) || (rightConstant && right)) {
		return true
	}
	return conditionHasMaskingConstant(binary.X, info) ||
		conditionHasMaskingConstant(binary.Y, info)
}

func conditionCallObjects(expression ast.Expr, info *types.Info, found map[types.Object]bool) {
	switch typed := expression.(type) {
	case *ast.CallExpr:
		if object := callObject(typed, info); object != nil {
			found[object] = true
		}
		conditionCallObjects(typed.Fun, info, found)
	case *ast.SelectorExpr:
		conditionCallObjects(typed.X, info, found)
	case *ast.ParenExpr:
		conditionCallObjects(typed.X, info, found)
	case *ast.UnaryExpr:
		conditionCallObjects(typed.X, info, found)
	case *ast.BinaryExpr:
		conditionCallObjects(typed.X, info, found)
		conditionCallObjects(typed.Y, info, found)
	case *ast.IndexExpr:
		conditionCallObjects(typed.X, info, found)
	}
}

func exactTestingTParameter(function *ast.FuncDecl, info *types.Info) (types.Object, error) {
	if function.Recv != nil || function.Type.Params == nil ||
		len(function.Type.Params.List) != 1 || function.Type.Results != nil {
		return nil, fmt.Errorf("must have exactly one *testing.T parameter and no result")
	}
	field := function.Type.Params.List[0]
	if len(field.Names) != 1 {
		return nil, fmt.Errorf("must name its exact *testing.T parameter")
	}
	parameter := info.Defs[field.Names[0]]
	variable, ok := parameter.(*types.Var)
	if !ok {
		return nil, fmt.Errorf("does not bind a *testing.T parameter")
	}
	pointer, ok := variable.Type().(*types.Pointer)
	if !ok {
		return nil, fmt.Errorf("does not bind a *testing.T parameter")
	}
	named, ok := pointer.Elem().(*types.Named)
	if !ok || named.Obj().Pkg() == nil || named.Obj().Pkg().Path() != "testing" ||
		named.Obj().Name() != "T" {
		return nil, fmt.Errorf("does not bind a *testing.T parameter")
	}
	return parameter, nil
}

func exactFailureCall(block *ast.BlockStmt, parameter types.Object, info *types.Info) bool {
	if len(block.List) != 1 {
		return false
	}
	expression, ok := block.List[0].(*ast.ExprStmt)
	if !ok {
		return false
	}
	call, ok := expression.X.(*ast.CallExpr)
	if !ok {
		return false
	}
	selector, ok := call.Fun.(*ast.SelectorExpr)
	if !ok {
		return false
	}
	receiver, ok := selector.X.(*ast.Ident)
	if !ok || info.Uses[receiver] != parameter {
		return false
	}
	object := callObject(call, info)
	if object == nil || object.Pkg() == nil || object.Pkg().Path() != "testing" {
		return false
	}
	switch selector.Sel.Name {
	case "Fatal", "Fatalf", "Error", "Errorf", "Fail", "FailNow":
		return true
	default:
		return false
	}
}

func closedFailureControl(function *ast.FuncDecl, info *types.Info) (map[types.Object]bool, error) {
	parameter, err := exactTestingTParameter(function, info)
	if err != nil {
		return nil, err
	}
	if function.Body == nil || len(function.Body.List) != 1 {
		return nil, fmt.Errorf("must contain exactly one reachable failure-control if statement")
	}
	guard, ok := function.Body.List[0].(*ast.IfStmt)
	if !ok || guard.Init != nil || guard.Else != nil || constantFalse(guard.Cond, info) ||
		constantTrue(guard.Cond, info) || conditionHasMaskingConstant(guard.Cond, info) ||
		!exactFailureCall(guard.Body, parameter, info) {
		return nil, fmt.Errorf("must contain one non-constant if without else whose body directly fails through its test parameter")
	}
	found := map[types.Object]bool{}
	conditionCallObjects(guard.Cond, info, found)
	return found, nil
}

func constantTrue(expression ast.Expr, info *types.Info) bool {
	value, ok := constantBool(expression, info)
	return ok && value
}

func expectedConformanceTests() map[string]bool {
	expected := make(map[string]bool, len(conformanceCalls))
	for _, contract := range conformanceCalls {
		expected[contract.testFunction] = true
	}
	return expected
}

func declaredIdentity(fileSet *token.FileSet, declaration ast.Decl) (symbolIdentity, bool, error) {
	switch typed := declaration.(type) {
	case *ast.FuncDecl:
		receiver, err := receiverName(fileSet, typed)
		if err != nil {
			return symbolIdentity{}, false, err
		}
		kind := "function"
		if typed.Recv != nil {
			kind = "method"
		}
		return symbolIdentity{typed.Name.Name, kind, receiver}, true, nil
	case *ast.GenDecl:
		if typed.Tok != token.TYPE || len(typed.Specs) != 1 {
			return symbolIdentity{}, false, nil
		}
		specification, ok := typed.Specs[0].(*ast.TypeSpec)
		if !ok {
			return symbolIdentity{}, false, nil
		}
		return symbolIdentity{specification.Name.Name, "type", ""}, true, nil
	default:
		return symbolIdentity{}, false, nil
	}
}

func closedConformanceDeclarations(
	files []*ast.File,
	testPaths map[string]bool,
	fileSet *token.FileSet,
) (map[string]*ast.FuncDecl, error) {
	expectedTests := expectedConformanceTests()
	testDeclarations := map[string]*ast.FuncDecl{}
	for _, file := range files {
		path := filepath.Clean(fileSet.Position(file.Package).Filename)
		isTest := testPaths[path]
		for _, declaration := range file.Decls {
			if generated, ok := declaration.(*ast.GenDecl); ok && generated.Tok == token.IMPORT {
				continue
			}
			identity, supported, err := declaredIdentity(fileSet, declaration)
			if err != nil {
				return nil, err
			}
			if isTest {
				if !supported || identity.Kind != "function" || !expectedTests[identity.Name] {
					return nil, fmt.Errorf("test source must contain only the fixed conformance test declarations")
				}
				function := declaration.(*ast.FuncDecl)
				if _, duplicate := testDeclarations[identity.Name]; duplicate {
					return nil, fmt.Errorf("test source duplicates fixed conformance declaration %s", identity.Name)
				}
				testDeclarations[identity.Name] = function
				continue
			}
			if !supported || fixedProductionByName[identity.Name] != identity {
				return nil, fmt.Errorf("production source contains an unexpected declaration or package initializer")
			}
		}
	}
	if len(testDeclarations) != len(expectedTests) {
		return nil, fmt.Errorf("test source omits one or more fixed conformance declarations")
	}
	return testDeclarations, nil
}

const conformanceReportPath = ".github/fmv3/fmv3-m1-06-conformance-report.json"

func mutationTargetPath(revision string, target symbolIdentity) (string, error) {
	data, err := source(revision, conformanceReportPath)
	if err != nil {
		return "", fmt.Errorf("base revision lacks the closed conformance report: %w", err)
	}
	var report conformanceReport
	if err := json.Unmarshal(data, &report); err != nil {
		return "", fmt.Errorf("base conformance report is invalid: %w", err)
	}
	path := ""
	count := 0
	for _, item := range report.Production {
		for _, descriptor := range item.Symbols {
			if descriptor.identity() == target {
				if descriptor.Signature == "" {
					return "", fmt.Errorf("mutation target descriptor has an empty signature")
				}
				path = filepath.Clean(item.Path)
				count++
			}
		}
	}
	if count != 1 {
		return "", fmt.Errorf("mutation target descriptor must be report-bound exactly once")
	}
	return path, nil
}

func exactGoEnvironment() []string {
	environment := make([]string, 0, len(os.Environ())+4)
	for _, entry := range os.Environ() {
		if strings.HasPrefix(entry, "GOOS=") || strings.HasPrefix(entry, "GOARCH=") ||
			strings.HasPrefix(entry, "CGO_ENABLED=") || strings.HasPrefix(entry, "GOWORK=") {
			continue
		}
		environment = append(environment, entry)
	}
	return append(environment, "GOOS=linux", "GOARCH=amd64", "CGO_ENABLED=0", "GOWORK=off")
}

func requireEqual(label string, actual, expected []string) error {
	if actual == nil {
		actual = []string{}
	}
	if expected == nil {
		expected = []string{}
	}
	if !reflect.DeepEqual(actual, expected) {
		return fmt.Errorf("%s differs: go list=%v report=%v", label, actual, expected)
	}
	return nil
}

func knownGoPlatforms() (map[string]bool, map[string]bool, error) {
	command := exec.Command("go", "tool", "dist", "list")
	command.Env = exactGoEnvironment()
	output, err := command.Output()
	if err != nil {
		return nil, nil, fmt.Errorf("go tool dist list failed: %w", err)
	}
	operatingSystems := map[string]bool{}
	architectures := map[string]bool{}
	for _, line := range strings.Fields(string(output)) {
		parts := strings.Split(line, "/")
		if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
			return nil, nil, fmt.Errorf("go tool dist list returned invalid platform %q", line)
		}
		operatingSystems[parts[0]] = true
		architectures[parts[1]] = true
	}
	if len(operatingSystems) == 0 || len(architectures) == 0 {
		return nil, nil, fmt.Errorf("go tool dist list returned no platforms")
	}
	return operatingSystems, architectures, nil
}

func hasImplicitPlatformSuffix(path string, operatingSystems, architectures map[string]bool) bool {
	name := filepath.Base(path)
	if !strings.HasSuffix(name, ".go") {
		return false
	}
	stem := strings.TrimSuffix(name, ".go")
	stem = strings.TrimSuffix(stem, "_test")
	separator := strings.LastIndexByte(stem, '_')
	if separator < 0 || separator == len(stem)-1 {
		return false
	}
	suffix := stem[separator+1:]
	return operatingSystems[suffix] || architectures[suffix]
}

func isBuildDirective(line, prefix string) bool {
	if !strings.HasPrefix(line, prefix) {
		return false
	}
	return len(line) == len(prefix) || line[len(prefix)] == ' ' || line[len(prefix)] == '\t'
}

func hasExplicitBuildConstraint(file *ast.File) bool {
	for _, group := range file.Comments {
		for _, comment := range group.List {
			line := strings.TrimSpace(comment.Text)
			if isBuildDirective(line, "//go:build") || isBuildDirective(line, "// +build") {
				return true
			}
		}
	}
	return false
}

func verifyConformance(reportPath string) error {
	data, err := os.ReadFile(reportPath)
	if err != nil {
		return err
	}
	var report conformanceReport
	if err := json.Unmarshal(data, &report); err != nil {
		return err
	}
	contract := report.GoList
	if contract.PackageDir != "." || contract.PackageQuery != "." ||
		contract.GOOS != "linux" || contract.GOARCH != "amd64" ||
		contract.CGOEnabled != "0" || contract.GOWORK != "off" {
		return fmt.Errorf("conformance report does not select the exact root package and fixed Go environment")
	}
	command := exec.Command("go", "list", "-json", "-compiled", contract.PackageQuery)
	command.Env = exactGoEnvironment()
	output, err := command.Output()
	if err != nil {
		return fmt.Errorf("go list failed: %w", err)
	}
	var listed goListResult
	if err := json.Unmarshal(output, &listed); err != nil {
		return err
	}
	root, err := filepath.Abs(".")
	if err != nil {
		return err
	}
	if filepath.Clean(listed.Dir) != filepath.Clean(root) || listed.Name != contract.PackageName ||
		listed.ImportPath != contract.ImportPath {
		return fmt.Errorf("go list package identity differs from the report")
	}
	comparisons := []struct {
		label    string
		actual   []string
		expected []string
	}{
		{"GoFiles", listed.GoFiles, contract.GoFiles},
		{"CompiledGoFiles", listed.CompiledGoFiles, contract.CompiledGoFiles},
		{"TestGoFiles", listed.TestGoFiles, contract.TestGoFiles},
		{"IgnoredGoFiles", listed.IgnoredGoFiles, contract.IgnoredGoFiles},
		{"CgoFiles", listed.CgoFiles, contract.CgoFiles},
		{"CFiles", listed.CFiles, contract.CFiles},
		{"CXXFiles", listed.CXXFiles, contract.CXXFiles},
		{"MFiles", listed.MFiles, contract.MFiles},
		{"HFiles", listed.HFiles, contract.HFiles},
		{"FFiles", listed.FFiles, contract.FFiles},
		{"SFiles", listed.SFiles, contract.SFiles},
		{"SwigFiles", listed.SwigFiles, contract.SwigFiles},
		{"SwigCXXFiles", listed.SwigCXXFiles, contract.SwigCXXFiles},
		{"SysoFiles", listed.SysoFiles, contract.SysoFiles},
		{"XTestGoFiles", listed.XTestGoFiles, contract.XTestGoFiles},
		{"IgnoredOtherFiles", listed.IgnoredOtherFiles, contract.IgnoredOtherFiles},
		{"EmbedPatterns", listed.EmbedPatterns, contract.EmbedPatterns},
		{"EmbedFiles", listed.EmbedFiles, contract.EmbedFiles},
		{"TestEmbedPatterns", listed.TestEmbedPatterns, contract.TestEmbedPatterns},
		{"TestEmbedFiles", listed.TestEmbedFiles, contract.TestEmbedFiles},
		{"XTestEmbedPatterns", listed.XTestEmbedPatterns, contract.XTestEmbedPatterns},
		{"XTestEmbedFiles", listed.XTestEmbedFiles, contract.XTestEmbedFiles},
	}
	for _, comparison := range comparisons {
		if err := requireEqual(comparison.label, comparison.actual, comparison.expected); err != nil {
			return err
		}
	}
	if len(contract.GoFiles) == 0 || len(contract.TestGoFiles) == 0 ||
		len(contract.IgnoredGoFiles)+len(contract.CgoFiles)+len(contract.CFiles)+
			len(contract.CXXFiles)+len(contract.MFiles)+len(contract.HFiles)+
			len(contract.FFiles)+len(contract.SFiles)+len(contract.SwigFiles)+
			len(contract.SwigCXXFiles)+len(contract.SysoFiles)+len(contract.XTestGoFiles)+
			len(contract.IgnoredOtherFiles)+len(contract.EmbedPatterns)+len(contract.EmbedFiles)+
			len(contract.TestEmbedPatterns)+len(contract.TestEmbedFiles)+
			len(contract.XTestEmbedPatterns)+len(contract.XTestEmbedFiles) != 0 {
		return fmt.Errorf("conformance package contains unsupported or excluded compiled inputs")
	}

	operatingSystems, architectures, err := knownGoPlatforms()
	if err != nil {
		return err
	}
	fileSet := token.NewFileSet()
	files := make([]*ast.File, 0, len(contract.GoFiles)+len(contract.TestGoFiles))
	testPaths := map[string]bool{}
	for _, path := range contract.TestGoFiles {
		testPaths[filepath.Clean(path)] = true
	}
	for _, path := range append(append([]string{}, contract.GoFiles...), contract.TestGoFiles...) {
		if hasImplicitPlatformSuffix(path, operatingSystems, architectures) {
			return fmt.Errorf("selected source %s has an implicit GOOS/GOARCH filename constraint", path)
		}
		content, readErr := os.ReadFile(path)
		if readErr != nil {
			return readErr
		}
		file, parseErr := parser.ParseFile(
			fileSet, path, content, parser.AllErrors|parser.ParseComments,
		)
		if parseErr != nil {
			return parseErr
		}
		if hasExplicitBuildConstraint(file) {
			return fmt.Errorf("selected source %s has an explicit build constraint", path)
		}
		files = append(files, file)
	}
	info := &types.Info{
		Defs:       map[*ast.Ident]types.Object{},
		Uses:       map[*ast.Ident]types.Object{},
		Selections: map[*ast.SelectorExpr]*types.Selection{},
		Types:      map[ast.Expr]types.TypeAndValue{},
	}
	configuration := types.Config{Importer: importer.Default()}
	if _, err := configuration.Check(contract.ImportPath, fileSet, files, info); err != nil {
		return fmt.Errorf("package type check failed: %w", err)
	}
	for identifier, object := range info.Defs {
		if object != nil && fixedProductionByName[identifier.Name].Name != "" &&
			testPaths[filepath.Clean(fileSet.Position(object.Pos()).Filename)] {
			return fmt.Errorf("test source shadows production contract name %s", identifier.Name)
		}
	}
	boundObjects := map[string]types.Object{}
	reportedSymbols := make([]symbolIdentity, 0, len(fixedProductionSymbols))
	for _, item := range report.Production {
		path := filepath.Clean(item.Path)
		for _, symbol := range item.Symbols {
			identity := symbol.identity()
			expected, ok := fixedProductionByName[identity.Name]
			if !ok || expected != identity || symbol.Signature == "" || len(symbol.Signature) > 256 {
				return fmt.Errorf("invalid production symbol descriptor %s", identity.Name)
			}
			var matches []types.Object
			for _, object := range info.Defs {
				if object == nil || filepath.Clean(fileSet.Position(object.Pos()).Filename) != path {
					continue
				}
				descriptor, supported := objectDescriptor(object)
				if supported && descriptor == symbol {
					matches = append(matches, object)
				}
			}
			if len(matches) != 1 {
				return fmt.Errorf("production symbol descriptor %s does not resolve exactly once", identity.Name)
			}
			if _, duplicate := boundObjects[identity.key()]; duplicate {
				return fmt.Errorf("duplicate production symbol descriptor %s", identity.Name)
			}
			boundObjects[identity.key()] = matches[0]
			reportedSymbols = append(reportedSymbols, identity)
		}
	}
	if !reflect.DeepEqual(reportedSymbols, fixedProductionSymbols) {
		return fmt.Errorf("production symbol descriptors are missing, reordered, or duplicated")
	}
	testDeclarations, err := closedConformanceDeclarations(files, testPaths, fileSet)
	if err != nil {
		return err
	}
	seenCases := map[string]bool{}
	for _, item := range report.Cases {
		expected, ok := conformanceCalls[item.CaseID]
		if !ok || seenCases[item.CaseID] || item.TestFunction != expected.testFunction ||
			testDeclarations[item.TestFunction] == nil {
			return fmt.Errorf("conformance case %s does not bind one exact test declaration", item.CaseID)
		}
		seenCases[item.CaseID] = true
		found, controlErr := closedFailureControl(testDeclarations[item.TestFunction], info)
		if controlErr != nil {
			return fmt.Errorf("%s has an invalid closed failure-control shape: %w", item.TestFunction, controlErr)
		}
		for _, required := range expected.required {
			identity := fixedProductionByName[required]
			object := boundObjects[identity.key()]
			if object == nil || !found[object] {
				return fmt.Errorf("%s does not failure-control exact production declaration %s", item.TestFunction, required)
			}
		}
	}
	if len(seenCases) != len(conformanceCalls) {
		return fmt.Errorf("conformance report omits one or more fixed cases")
	}
	return nil
}

func main() {
	caseID := flag.String("case", "", "exact mutation case")
	base := flag.String("base", "", "GREEN parent revision")
	mutant := flag.String("mutant", "", "mutant revision")
	verifyReport := flag.String("verify-conformance", "", "verify exact conformance report and Go package")
	flag.Parse()
	if *verifyReport != "" {
		if *caseID != "" || *base != "" || *mutant != "" {
			fmt.Fprintln(os.Stderr, "conformance and mutation modes are mutually exclusive")
			os.Exit(2)
		}
		if err := verifyConformance(*verifyReport); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println("validated exact M1-06 root package, compiled inputs, and production API calls")
		return
	}
	contract, ok := caseContracts[*caseID]
	if !ok || *base == "" || *mutant == "" {
		fmt.Fprintln(os.Stderr, "invalid mutation guard arguments")
		os.Exit(2)
	}
	targetPath, err := mutationTargetPath(*base, contract.target)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	output, err := git("diff", "--name-only", "-z", *base, *mutant)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	paths := strings.Split(strings.TrimSuffix(string(output), "\x00"), "\x00")
	if len(paths) != 1 {
		fmt.Fprintln(os.Stderr, "mutation must touch exactly one file: the production Go target")
		os.Exit(1)
	}
	changed := map[string]bool{}
	var beforeDecls map[string]string
	var afterDecls map[string]string
	for _, path := range paths {
		if strings.HasSuffix(path, "_test.go") || !strings.HasSuffix(path, ".go") ||
			filepath.Clean(path) != targetPath {
			fmt.Fprintln(os.Stderr, "mutation touched non-production Go source")
			os.Exit(1)
		}
		before, beforeErr := source(*base, path)
		after, afterErr := source(*mutant, path)
		if beforeErr != nil || afterErr != nil {
			fmt.Fprintln(os.Stderr, "mutation must modify existing production Go files")
			os.Exit(1)
		}
		beforeDecls, beforeErr = declarations(path, before)
		afterDecls, afterErr = declarations(path, after)
		if beforeErr != nil || afterErr != nil {
			fmt.Fprintln(os.Stderr, "mutation source does not parse")
			os.Exit(1)
		}
		beforeStart, beforeEnd, beforeSpanErr := declarationSpan(path, before, contract.target)
		afterStart, afterEnd, afterSpanErr := declarationSpan(path, after, contract.target)
		if beforeSpanErr != nil || afterSpanErr != nil {
			fmt.Fprintln(os.Stderr, "mutation target declaration is absent or ambiguous")
			os.Exit(1)
		}
		beforeTarget := before[beforeStart:beforeEnd]
		afterTarget := after[afterStart:afterEnd]
		if bytes.Count(beforeTarget, []byte(contract.before)) != 1 ||
			bytes.Count(beforeTarget, []byte(contract.after)) != 0 ||
			bytes.Count(afterTarget, []byte(contract.before)) != 0 ||
			bytes.Count(afterTarget, []byte(contract.after)) != 1 {
			fmt.Fprintf(os.Stderr, "mutation must replace only the exact %s return expression\n", contract.target.Name)
			os.Exit(1)
		}
		expectedTarget := bytes.Replace(
			beforeTarget, []byte(contract.before), []byte(contract.after), 1,
		)
		expected := make([]byte, 0, len(before)-len(beforeTarget)+len(expectedTarget))
		expected = append(expected, before[:beforeStart]...)
		expected = append(expected, expectedTarget...)
		expected = append(expected, before[beforeEnd:]...)
		if !bytes.Equal(after, expected) {
			fmt.Fprintf(os.Stderr, "mutation must be exactly the case return replacement for %s\n", contract.target.Name)
			os.Exit(1)
		}
		for name, oldValue := range beforeDecls {
			newValue, exists := afterDecls[name]
			if !exists || oldValue != newValue {
				changed[name] = true
			}
		}
		for name := range afterDecls {
			if _, exists := beforeDecls[name]; !exists {
				changed[name] = true
			}
		}
	}
	names := make([]string, 0, len(changed))
	for name := range changed {
		names = append(names, name)
	}
	sort.Strings(names)
	targetKey := contract.target.key()
	if len(names) != 1 || names[0] != targetKey {
		fmt.Fprintf(os.Stderr, "mutation must change only the exact report-bound case target, changed %v\n", names)
		os.Exit(1)
	}
	fmt.Printf("validated executable AST mutation for %s: %v\n", *caseID, names)
}

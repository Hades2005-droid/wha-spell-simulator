using System.Text.Json;
using ShadowGarden.RecursiveBridge;

var argumentsMap = ParseArguments(args);
var nodeCount = GetInt(argumentsMap, "nodes", RecursiveNodeBridgeOptions.DefaultNodeCount);
var gain = GetDouble(argumentsMap, "gain", 1.0);
var cycles = GetInt(argumentsMap, "cycles", 1);
var duration = GetDouble(argumentsMap, "duration", 0.0);
var continuous = argumentsMap.ContainsKey("continuous");

if (continuous && duration <= 0)
{
    Console.Error.WriteLine("--continuous requires a positive --duration safety limit");
    return 2;
}

try
{
    await using var bridge = new RecursiveNodeBridge(new RecursiveNodeBridgeOptions(
        nodeCount: nodeCount,
        gain: gain,
        routeName: GetString(argumentsMap, "route-name", "local-open-weights"),
        routeModel: GetString(argumentsMap, "route-model", "deepseek-local"),
        routeEndpoint: GetString(argumentsMap, "route-endpoint", "http://127.0.0.1:11434/v1")));

    var snapshot = await bridge.RunAsync(
        maxCycles: continuous ? null : cycles,
        maxDuration: continuous ? TimeSpan.FromSeconds(duration) : null);
    var output = JsonSerializer.Serialize(snapshot, new JsonSerializerOptions
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    });
    var statusFile = GetString(argumentsMap, "status-file", "/tmp/shadow_garden_recursive_node_status.json");
    await File.WriteAllTextAsync(statusFile, output + Environment.NewLine);
    Console.WriteLine(output);
}
catch (ArgumentException exception)
{
    Console.Error.WriteLine(exception.Message);
    return 2;
}

return 0;

static Dictionary<string, string> ParseArguments(string[] args)
{
    var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    for (var index = 0; index < args.Length; index++)
    {
        if (!args[index].StartsWith("--", StringComparison.Ordinal))
            continue;
        var key = args[index][2..];
        if (key == "continuous")
        {
            result[key] = "true";
            continue;
        }
        if (index + 1 < args.Length && !args[index + 1].StartsWith("--", StringComparison.Ordinal))
            result[key] = args[++index];
    }
    return result;
}

static string GetString(Dictionary<string, string> values, string key, string fallback)
    => values.TryGetValue(key, out var value) ? value : fallback;

static int GetInt(Dictionary<string, string> values, string key, int fallback)
    => values.TryGetValue(key, out var value) && int.TryParse(value, out var parsed) ? parsed : fallback;

static double GetDouble(Dictionary<string, string> values, string key, double fallback)
    => values.TryGetValue(key, out var value) && double.TryParse(value, out var parsed) ? parsed : fallback;

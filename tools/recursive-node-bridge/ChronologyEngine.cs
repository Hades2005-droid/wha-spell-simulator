using System;
using System.Collections.Generic;

namespace ShadowGarden.RecursiveBridge;

public sealed record Frequency(
    string Source,
    int Raw,
    int Reduced,
    string Archetype,
    string Lens,
    bool Master);

public static class ChronologyEngine
{
    private static readonly HashSet<int> MasterNumbers = new() { 11, 22, 33 };

    private static readonly IReadOnlyDictionary<int, string> Archetypes = new Dictionary<int, string>
    {
        [0] = "Wuji / Vacuum",
        [1] = "Magician",
        [2] = "High Priestess",
        [3] = "Empress",
        [4] = "Emperor",
        [5] = "Hierophant",
        [6] = "Lovers",
        [7] = "Chariot",
        [8] = "Strength",
        [9] = "Hermit",
        [10] = "Wheel",
        [11] = "Justice / Tensegrity",
        [12] = "Hanged Man",
        [13] = "Death / Transition",
        [14] = "Temperance",
        [15] = "Devil / Apophenia Shield",
        [16] = "Tower / Structural Reset",
        [17] = "Star",
        [18] = "Moon",
        [19] = "Sun",
        [20] = "Judgement",
        [21] = "World",
        [22] = "Master Builder",
    };

    private static readonly IReadOnlyDictionary<int, string> SymbolicVectors = new Dictionary<int, string>
    {
        [23] = "Sovereign Friction",
        [24] = "Localized Harmony",
        [25] = "Chariot's Logic",
        [26] = "Engine's Output",
        [27] = "Queen's Code",
        [28] = "Perfect Mass",
        [29] = "Orbit Prime",
        [30] = "Trinity Fold",
        [31] = "Prime Isolation",
        [32] = "Binary Collapse",
        [33] = "Ascended Flow",
        [34] = "Fibonacci Drift",
        [35] = "Pentagonal Trap",
        [36] = "Panopticon",
        [37] = "Ascended Observer",
        [38] = "Isotope Decay",
        [39] = "Late-Stage Syzygy",
        [40] = "Quarantine Zone",
        [41] = "Event Horizon",
        [42] = "Sovereign Anchor",
    };

    public static int DigitSum(int value)
    {
        var remaining = Math.Abs(value);
        var sum = 0;
        do
        {
            sum += remaining % 10;
            remaining /= 10;
        } while (remaining > 0);
        return sum;
    }

    public static int ReduceFrequency(int value, bool preserveMaster = true)
    {
        var current = Math.Abs(value);
        while (current > 9)
        {
            if (preserveMaster && MasterNumbers.Contains(current))
                return current;
            current = DigitSum(current);
        }
        return current;
    }

    public static Frequency Classify(int raw, string source = "value")
    {
        var reduced = ReduceFrequency(raw);
        var isVector = SymbolicVectors.TryGetValue(raw, out var vectorLabel);
        var archetype = isVector
            ? vectorLabel!
            : Archetypes.TryGetValue(reduced, out var label) ? label : "Unclassified";
        return new Frequency(
            source,
            raw,
            reduced,
            archetype,
            isVector ? "user_defined_symbolic_vector" : "symbolic_tarot_reduction",
            MasterNumbers.Contains(raw) || MasterNumbers.Contains(reduced));
    }

    public static IReadOnlyDictionary<string, Frequency> AnalyzeDate(DateOnly value)
    {
        var rawValues = new Dictionary<string, int>
        {
            ["micro_digit_sum"] = DigitSum(value.Month) + DigitSum(value.Day),
            ["micro_number_sum"] = value.Month + value.Day,
            ["macro_digit_sum"] = DigitSum(value.Month) + DigitSum(value.Day) + DigitSum(value.Year),
            ["macro_number_sum"] = value.Month + value.Day + value.Year,
            ["year_digit_sum"] = DigitSum(value.Year),
            ["year_number"] = value.Year,
            ["month"] = value.Month,
            ["day_digit_sum"] = DigitSum(value.Day),
            ["day_number"] = value.Day,
            ["month_year_digit_sum"] = DigitSum(value.Month) + DigitSum(value.Year),
            ["day_year_digit_sum"] = DigitSum(value.Day) + DigitSum(value.Year),
        };

        var result = new Dictionary<string, Frequency>();
        foreach (var pair in rawValues)
            result[pair.Key] = Classify(pair.Value, pair.Key);
        return result;
    }
}

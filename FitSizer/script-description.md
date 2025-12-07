# FitSizer - Fusion 360 Script

## Purpose

FitSizer generates a set of U-shaped wrench/gauge bodies for measuring or testing fit tolerances. Each wrench has a different mouth opening size, with the size engraved on the handle for easy identification.

This is useful for:
- Finding the correct size for nuts, bolts, or other hardware
- Testing 3D printer tolerances and fit accuracy
- Creating sizing gauges for custom parts

## How It Works

The script creates multiple wrench-shaped bodies arranged in a row. Each wrench has:
1. A **U-shaped mouth opening** - the measurement dimension
2. A **handle** with the size engraved into the top surface

## Configuration Parameters

### Mouth Size Range
| Parameter | Description | Default |
|-----------|-------------|---------|
| `mouth_size_min` | Starting mouth width (mm) | 2.0 |
| `mouth_size_max` | Ending mouth width (mm) | 4.0 |
| `mouth_size_increment` | Step between sizes (mm) | 0.5 |

Example: 2.0 to 4.0 by 0.5 generates: 2.0, 2.5, 3.0, 3.5, 4.0

### Wrench Geometry
| Parameter | Description | Default |
|-----------|-------------|---------|
| `jaw_depth` | Depth of the U-shaped mouth (mm) | 5.0 |
| `jaw_thickness` | Thickness of the jaw walls (mm) | 2.0 |
| `handle_height` | Height of the handle area (mm) | 12.0 |
| `extrude_depth` | Thickness of the wrench body (mm) | 2.0 |
| `spacing` | Distance between wrenches (mm) | 20.0 |

### Text Engraving
| Parameter | Description | Default |
|-----------|-------------|---------|
| `text_height` | Height of engraved text (mm) | 2.5 |
| `emboss_depth` | Depth of text engraving (mm) | 0.5 |

## Wrench Shape

```
    +-----------------+
    |                 |
    |     [3.0]       |   <- Handle with engraved size
    |                 |
    +---+       +-----+
        |       |         <- Jaw walls (jaw_thickness)
        |       |
        +-------+         <- Mouth opening (mouth_width)
```

## Output

- Creates separate solid bodies for each size
- Each body is named with its mouth size (e.g., "2.0", "2.5", "3.0")
- Bodies are arranged left-to-right with consistent spacing
- Text is engraved (cut into) the top surface of the handle

## Usage

1. Open Fusion 360
2. Create a new design or open an existing one
3. Run the FitSizer script from Scripts and Add-Ins
4. The wrenches are created in the active component
5. Export/3D print as needed

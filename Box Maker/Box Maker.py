"""This file acts as the main module for this script."""
import traceback
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()
ui  = app.userInterface

def run(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Fusion design first.")
            return
        um = design.unitsManager
        root = design.rootComponent

        # ---------- Parameter names & defaults (mm) ----------
        DEFAULTS_MM = dict(
            Length=100.0, Width=60.0, Height=60.0,
            Thickness=3.0, Kerf=0.10, TabWidth=12.0, Gap=3.0
        )
        NAME_CHOICES = {
            "Length":   ["CtrlBoxLength","BoxLength","Length"],
            "Width":    ["CtrlBoxWidth","BoxWidth","Width"],
            "Height":   ["CtrnBoxHeigh","CtrlBoxHeight","BoxHeight","Height"],
            "Thickness":["BoardThickness","MaterialThickness","Thickness"],
            "Kerf":     ["Kerf","LaserKerf"],
        }

        def mm_to_internal(val_mm: float) -> float:
            # Fusion uses internal cm—convert reliably
            return um.evaluateExpression(f"{val_mm} mm", "cm")

        def get_or_create_len(names, default_mm, comment):
            for n in names:
                p = design.userParameters.itemByName(n)
                if p: return p.value, n
            n = names[0]
            p = design.userParameters.add(
                n, adsk.core.ValueInput.createByString(f"{default_mm} mm"), "mm", comment
            )
            return p.value, n

        L, L_name = get_or_create_len(NAME_CHOICES["Length"],   DEFAULTS_MM["Length"],   "Box length")
        W, W_name = get_or_create_len(NAME_CHOICES["Width"],    DEFAULTS_MM["Width"],    "Box width")
        H, H_name = get_or_create_len(NAME_CHOICES["Height"],   DEFAULTS_MM["Height"],   "Box height")
        T, T_name = get_or_create_len(NAME_CHOICES["Thickness"],DEFAULTS_MM["Thickness"],"Material thickness")
        K, K_name = get_or_create_len(NAME_CHOICES["Kerf"],     DEFAULTS_MM["Kerf"],     "Kerf per side")

        TAB_W = mm_to_internal(DEFAULTS_MM["TabWidth"])
        GAP   = mm_to_internal(DEFAULTS_MM["Gap"])

        # ---------- New sketch ----------
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = "Tabbed Box (T net)"

        def pt(x, y): return adsk.core.Point3D.create(x, y, 0)

        # Panel with real edges (not construction)
        # returns dict with points and the line objects in order: bottom, right, top, left
        def panel_rect(x0, y0, w, h):
            p0 = pt(x0,     y0)      # BL
            p1 = pt(x0 + w, y0)      # BR
            p2 = pt(x0 + w, y0 + h)  # TR
            p3 = pt(x0,     y0 + h)  # TL
            lines = [
                sk.sketchCurves.sketchLines.addByTwoPoints(p0, p1),  # bottom
                sk.sketchCurves.sketchLines.addByTwoPoints(p1, p2),  # right
                sk.sketchCurves.sketchLines.addByTwoPoints(p2, p3),  # top
                sk.sketchCurves.sketchLines.addByTwoPoints(p3, p0),  # left
            ]
            return dict(pts=[p0,p1,p2,p3], lines=lines)

        # Rectangular finger path that REPLACES a straight edge:
        # we set the straight edge to construction, then draw the fingered outline over it.
        def finger_edge(start, end, out_vec: adsk.core.Vector3D, male=True, inner_fit=False):
            dir_vec = adsk.core.Vector3D.create(end.x - start.x, end.y - start.y, 0)
            Ledge = dir_vec.length
            if Ledge <= 1e-7: return
            dir_vec.normalize()
            out = adsk.core.Vector3D.create(out_vec.x, out_vec.y, 0); out.normalize()

            usable = max(1e-7, Ledge - (T if inner_fit else 0.0))
            n = max(1, int(round(usable / TAB_W)))
            if n % 2 == 0: n += 1
            pitch = usable / n
            half = pitch * 0.5

            cur = adsk.core.Point3D.create(start.x, start.y, 0)
            for i in range(n):
                # first half along base
                s1 = adsk.core.Point3D.create(cur.x + dir_vec.x*half, cur.y + dir_vec.y*half, 0)
                sk.sketchCurves.sketchLines.addByTwoPoints(cur, s1)

                is_tab = ((i % 2) == 0) == male
                width_bias = (K if is_tab else -K)  # press-fit: tabs wider, slots narrower

                # out/in by T
                bump = adsk.core.Point3D.create(
                    s1.x + out.x*(T if is_tab else -T),
                    s1.y + out.y*(T if is_tab else -T), 0
                )
                sk.sketchCurves.sketchLines.addByTwoPoints(s1, bump)

                # second half + bias
                s2 = adsk.core.Point3D.create(
                    bump.x + dir_vec.x*(half + width_bias),
                    bump.y + dir_vec.y*(half + width_bias), 0
                )
                sk.sketchCurves.sketchLines.addByTwoPoints(bump, s2)

                # return to baseline
                back = adsk.core.Point3D.create(
                    s2.x - out.x*(T if is_tab else -T),
                    s2.y - out.y*(T if is_tab else -T), 0
                )
                sk.sketchCurves.sketchLines.addByTwoPoints(s2, back)
                cur = back

            # close to the original end if inner-fit shortened the run (construction so it doesn't block profiles)
            if inner_fit:
                tail = sk.sketchCurves.sketchLines.addByTwoPoints(cur, end)
                tail.isConstruction = True

        # coords (T layout)
        xFront = W + GAP
        yFront = H + GAP
        xLeft  = 0
        xRight = xFront + L + GAP
        xBack  = xRight + W + GAP
        yTop   = yFront + H + GAP
        yBottom= 0

        front  = panel_rect(xFront,  yFront,  L, H)
        leftp  = panel_rect(xLeft,   yFront,  W, H)
        rightp = panel_rect(xRight,  yFront,  W, H)
        back   = panel_rect(xBack,   yFront,  L, H)
        top    = panel_rect(xFront,  yTop,    L, H)
        bottom = panel_rect(xFront,  yBottom, L, H)

        # vectors
        up    = adsk.core.Vector3D.create(0,  1, 0)
        down  = adsk.core.Vector3D.create(0, -1, 0)
        vecR  = adsk.core.Vector3D.create(1,  0, 0)
        vecL  = adsk.core.Vector3D.create(-1, 0, 0)

        # helper to replace a panel edge with fingers
        # edge index: 0=bottom, 1=right, 2=top, 3=left
        def replace_edge(panel, edge_index, out_vec, male, inner_fit):
            line = panel["lines"][edge_index]
            pstart = line.startSketchPoint.geometry
            pend   = line.endSketchPoint.geometry
            line.isConstruction = True  # keep it as reference, but don't block profile
            finger_edge(pstart, pend, out_vec, male=male, inner_fit=inner_fit)

        # Ring seams (Front-Right-Back-Left)
        replace_edge(front,  1, vecR, True,  False)  # Front right M/o
        replace_edge(rightp, 3, vecL, False, True)   # Right left F/i

        replace_edge(rightp, 1, vecR, True,  False)  # Right right M/o
        replace_edge(back,   3, vecL, False, True)   # Back left F/i

        replace_edge(back,   1, vecR, True,  False)  # Back right M/o
        replace_edge(leftp,  3, vecL, False, True)   # Left left F/i

        replace_edge(leftp,  1, vecR, True,  False)  # Left right M/o
        replace_edge(front,  3, vecL, False, True)   # Front left F/i

        # Top (M/i) with side mates (F/o)
        replace_edge(top,   0, up,    True,  True)   # Top bottom -> Front top
        replace_edge(front, 2, down,  False, False)

        replace_edge(top,   1, vecR,  True,  True)   # Top right -> Right top
        replace_edge(rightp,2, up,    False, False)

        replace_edge(top,   2, up,    True,  True)   # Top top -> Back top
        replace_edge(back,  0, down,  False, False)

        replace_edge(top,   3, vecL,  True,  True)   # Top left -> Left top
        replace_edge(leftp, 2, up,    False, False)

        # Bottom (M/i) with side mates (F/o)
        replace_edge(bottom,2, up,    True,  True)   # Bottom top -> Front bottom
        replace_edge(front, 0, up,    False, False)

        replace_edge(bottom,1, vecR,  True,  True)   # Bottom right -> Right bottom
        replace_edge(rightp,0, up,    False, False)

        replace_edge(bottom,0, down,  True,  True)   # Bottom bottom -> Back bottom
        replace_edge(back,  2, up,    False, False)

        replace_edge(bottom,3, vecL,  True,  True)   # Bottom left -> Left bottom
        replace_edge(leftp, 0, up,    False, False)

        # ---------- turn profiles into solid test parts ----------
        profs = [p for p in sk.profiles]  # snapshot; profiles collection is dynamic
        if not profs:
            ui.messageBox("No profiles found—check for tiny gaps.")
            return

        extrudes = root.features.extrudeFeatures
        dist = adsk.core.ValueInput.createByReal(T)  # internal cm distance
        for pr in profs:
            ext = extrudes.addSimple(pr, dist, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            # Name bodies for clarity
            try:
                ext.bodies.item(0).name = "Panel"
            except:
                pass

        ui.messageBox(
            "Tabbed T-pattern created and extruded.\n"
            f"Params: {L_name} / {W_name} / {H_name} / {T_name} / {K_name}\n"
            "Use Move/Copy to dry-fit, or Assemble > Joints."
        )

    except:
        app.log(f"Failed:\n{traceback.format_exc()}")

def stop(context):
    pass

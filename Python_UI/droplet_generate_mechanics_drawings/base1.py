import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_yulang_system():
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Colors
    c_body = '#dcdcdc'
    c_water = '#87cefa'
    c_swab = '#f5deb3'
    c_bottle = '#b0e0e6'
    c_silicone = '#ff9933'
    
    # 1. Draw Water (Z=5 to Z=14)
    # Left pit water
    ax.add_patch(patches.Rectangle((26, 5), 8, 3, facecolor=c_water, edgecolor='none', alpha=0.7))
    # Channel and right side water (Z=8 to Z=14)
    ax.add_patch(patches.Rectangle((26, 8), 78, 6, facecolor=c_water, edgecolor='none', alpha=0.7))

    # 2. Draw Solid Body (Using shapes to form the cross section)
    walls = [
        # Base Z=0 to 8
        patches.Rectangle((10, 0), 100, 5, facecolor=c_body, edgecolor='black'), # bottom solid
        patches.Rectangle((10, 5), 16, 3, facecolor=c_body, edgecolor='black'),  # left of pit
        patches.Rectangle((34, 5), 76, 3, facecolor=c_body, edgecolor='black'),  # right of pit
        
        # Water Channel level Z=8 to 20
        patches.Rectangle((10, 8), 16, 12, facecolor=c_body, edgecolor='black'), # left outer wall
        patches.Rectangle((104, 8), 6, 12, facecolor=c_body, edgecolor='black'), # right outer wall
        
        # Left Flange Level Z=20 to 32
        patches.Rectangle((10, 20), 16, 12, facecolor=c_body, edgecolor='black'), # left outer
        patches.Rectangle((34, 20), 26, 12, facecolor=c_body, edgecolor='black'), # left inner to center
        
        # Right Thread Level Z=20 to 34
        patches.Rectangle((60, 20), 16, 14, facecolor=c_body, edgecolor='black'), # right inner
        patches.Rectangle((104, 20), 6, 14, facecolor=c_body, edgecolor='black'), # right outer
        
        # Right Counterbore Z=34 to 39
        patches.Rectangle((60, 34), 12.5, 5, facecolor=c_body, edgecolor='black'),
        patches.Rectangle((107.5, 34), 2.5, 5, facecolor=c_body, edgecolor='black'),
        
        # Left Step Z=32 to 33
        patches.Rectangle((22, 32), 4, 1, facecolor=c_body, edgecolor='black'), # left part of step
        patches.Rectangle((34, 32), 4, 1, facecolor=c_body, edgecolor='black'), # right part of step
    ]
    for w in walls:
        ax.add_patch(w)

    # 3. Draw Blind Hole (Screw hole) Z=22 to 32
    # Place it at X=15 (width 2.6)
    ax.add_patch(patches.Rectangle((13.7, 22), 2.6, 10, facecolor='white', edgecolor='black'))

    # 4. Draw Cotton Swab Z=5 to Z=45
    ax.add_patch(patches.Rectangle((26.15, 5), 7.7, 40, facecolor=c_swab, edgecolor='#cd853f', lw=2))
    
    # 5. Draw Silicone Pad Z=34 to Z=35 (compressed)
    ax.add_patch(patches.Rectangle((72.5, 34), 35, 1, facecolor=c_silicone, edgecolor='black', hatch='//'))
    
    # 6. Draw Cola Bottle
    # Flange at Z=35
    ax.add_patch(patches.Rectangle((73, 35), 34, 2, facecolor=c_bottle, edgecolor='#1f77b4', alpha=0.8))
    # Neck from Z=14 to Z=35
    ax.add_patch(patches.Rectangle((76, 14), 28, 21, facecolor=c_bottle, edgecolor='#1f77b4', alpha=0.5))
    # Upper bottle body (cut off)
    ax.add_patch(patches.Rectangle((75, 37), 30, 8, facecolor=c_bottle, edgecolor='#1f77b4', alpha=0.5))

    # 7. Add Z-level dashed lines and labels
    z_levels = {
        0: 'Z=0 (Base)',
        5: 'Z=5 (Pit Bottom)',
        8: 'Z=8 (Channel Bottom)',
        14: 'Z=14 (Water Level/Bottle Tip)',
        20: 'Z=20 (Channel Top)',
        22: 'Z=22 (Blind Hole Bottom)',
        32: 'Z=32 (Left Flange Top)',
        33: 'Z=33 (Positioning Step)',
        34: 'Z=34 (Right Hard Limit)',
        39: 'Z=39 (Right Top)'
    }
    
    for z, label in z_levels.items():
        ax.axhline(y=z, color='red', linestyle='--', lw=1, alpha=0.6)
        ax.text(5, z, label, color='red', va='center', ha='right', fontweight='bold')

    # Specific callouts
    ax.annotate('M3x16 Screw Hole\n(Safe depth)', xy=(15, 22), xytext=(5, 26),
                arrowprops=dict(arrowstyle="->", color="black"))
    ax.annotate('6mm Air Buffer', xy=(50, 17), xytext=(50, 17), ha='center', va='center', fontweight='bold')
    ax.annotate('6mm Water Depth', xy=(50, 11), xytext=(50, 11), ha='center', va='center', fontweight='bold', color='navy')
    ax.annotate('Cotton Swab\n(Total 40mm)', xy=(30, 40), xytext=(45, 42),
                arrowprops=dict(arrowstyle="->", color="black"), ha='center')
    ax.annotate('1mm Compressed Silicone', xy=(100, 34.5), xytext=(115, 32),
                arrowprops=dict(arrowstyle="->", color="black"))
    
    # Setting up axes
    ax.set_xlim(-10, 125)
    ax.set_ylim(-2, 48)
    ax.axis('off')
    plt.title('【Yulang System】 Absolute Z-Axis Global Architecture', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('yulang_global_architecture.png', dpi=300)
    plt.show()

draw_yulang_system()
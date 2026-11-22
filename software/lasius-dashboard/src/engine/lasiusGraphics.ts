/**
 * 3D WebGL Digital Twin & 2D Orthographic Projection Engine (`lasius-dashboard/src/engine/lasiusGraphics.ts`).
 *
 * Purpose & Role:
 *   Encapsulates all imperative Three.js 3D rendering and HTML5 Canvas 2D CAD
 *   orthographic projections (Top XY, Front XZ, Side YZ) outside of Vue's
 *   reactivity proxy (`shallowRef` in `App.vue`) for 60 FPS real-time performance.
 *
 * FreeCAD v2 Architecture Sync:
 *   - Loads the 29 canonical FreeCAD v2 Binary STL meshes (`/meshes/*.stl` from
 *     `hardware/mechanics/export/urdf/meshes/`) via `STLLoader` with exact
 *     link-local coordinate transforms (`det = +1`, outward normals):
 *       * Chassis v2: `body_bottom`, `body_top`, `chassis_core`, `chassis_belly_pan`,
 *         `chassis_rpi_mount`, `chassis_canopy` (translucent acrylic), `chassis_service_cover`,
 *         `rpi4_model_b`, `vl53l5cx_board`.
 *       * Coxa v2: `coxa_{left,right}` (unified 45° A-truss cheeks), `coxa_servo_{left,right}`,
 *         `femur_servo_{left,right}`.
 *       * Femur v2: `femur_{left,right}` (45° A-truss monocoque box girder), `femur_cover_{left,right}`.
 *       * Tibia & Tarsus v2: `tibia_{left,right}` (45° A-truss servo cage, Krallen-Sichel teardrop,
 *         2.50 mm lower web taper), `tibia_cover_{left,right}`, `knee_servo_{left,right}`,
 *         `tarsus_{left,right}` (3D-exoskeleton), `tarsus_shoe_{left,right}` (compact Kufe).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import {
  CHASSIS_HULL_CONTOUR,
  CHASSIS_COXA_HOLES,
  CHASSIS_SPECS,
  COXA_SPECS,
  TIBIA_SPECS
} from './cadGeometries';

export interface GraphicsContainers {
  threeContainer: HTMLElement;
  topCanvas: HTMLCanvasElement;
  sideCanvas: HTMLCanvasElement;
  frontCanvas: HTMLCanvasElement;
}

export interface GraphicsCallbacks {
  onSelectLeg: (legKey: string) => void;
  onHoverJoint: (joint: 'coxa' | 'femur' | 'tibia' | null) => void;
}

export class LasiusGraphicsEngine {
  private containers: GraphicsContainers;
  private callbacks: GraphicsCallbacks;

  // Three.js scene
  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private controls!: OrbitControls;
  private animFrameId: number | null = null;
  private resizeObserver: ResizeObserver | null = null;

  // 2D Canvas contexts
  private topCtx!: CanvasRenderingContext2D;
  private sideCtx!: CanvasRenderingContext2D;
  private frontCtx!: CanvasRenderingContext2D;

  // 2D Interaction hit points maps
  private topViewLegPoints: Record<string, any> = {};
  private sideViewLegPoints: Record<string, any> = {};
  private frontViewLegPoints: Record<string, any> = {};

  // Three.js Materials & Geometries
  private chassisMat!: THREE.MeshStandardMaterial;
  private canopyMat!: THREE.MeshStandardMaterial;
  private pcbGreenMat!: THREE.MeshStandardMaterial;
  private pcbRedMat!: THREE.MeshStandardMaterial;
  private tarsusNeutralMat!: THREE.MeshStandardMaterial;
  private kufeNeutralMat!: THREE.MeshStandardMaterial;
  private coverNeutralMat!: THREE.MeshStandardMaterial;
  private eyeMat!: THREE.MeshStandardMaterial;
  private hardwareMat!: THREE.MeshStandardMaterial;
  private carbonPlateMat!: THREE.MeshStandardMaterial;
  private brassMat!: THREE.MeshStandardMaterial;
  private aluSpacerMat!: THREE.MeshStandardMaterial;
  private bearingMat!: THREE.MeshStandardMaterial;
  private chassisAxisMat!: THREE.MeshStandardMaterial;
  private chassisMountActiveMat!: THREE.MeshStandardMaterial;
  private legNeutralMat!: THREE.MeshStandardMaterial;
  private jointNeutralMat!: THREE.MeshStandardMaterial;
  private legSelectedMat!: THREE.MeshStandardMaterial;
  private jointSelectedMat!: THREE.MeshStandardMaterial;
  private legActiveSegmentMat!: THREE.MeshStandardMaterial;
  private jointActiveMat!: THREE.MeshStandardMaterial;
  private axisGuideMat!: THREE.MeshBasicMaterial;

  // Cached FreeCAD v2 STL BufferGeometries (loaded asynchronously via STLLoader)
  private stlGeometries: Record<string, THREE.BufferGeometry> = {};
  private stlLoadingStarted = false;
  private stlLoadedReady = false;

  // 3D Meshes map
  private robotRootGroup!: THREE.Group;
  private groundGridGroup!: THREE.Group;
  private groundGrid!: THREE.GridHelper;
  private robot3DMeshes: any = {
    body: null,
    legs: {},
    axesGroup: null,
    axes: null,
    arcsGroup: null,
    mountRings: {},
    trailsGroup: null,
    contactRings: {},
    trailLines: {}
  };
  private motionRangeArcs: any = {};
  private lastSelectedLegKinematics: any = null;
  private showFootTrails = true;
  private footTrailHistory: Record<string, THREE.Vector3[]> = {};
  private readonly MAX_TRAIL_POINTS = 55;

  // Kinematic Ground Anchoring & World Odometry state (with pre-allocated 50 Hz scratch vectors)
  private groundLocked = true;
  private chassisWorldZ = 0.0;
  private chassisWorldQuat = new THREE.Quaternion();
  private prevWorldFeet: Record<string, { x: number; y: number; z: number }> = {};
  private groundYaw = 0.0;
  private groundLocalX = 0.0;
  private groundLocalZ = 0.0;
  private readonly WORLD_UP = new THREE.Vector3(0, 1, 0);
  private readonly scratchPlaneNormal = new THREE.Vector3(0, 1, 0);
  private readonly scratchTargetQuat = new THREE.Quaternion();
  private readonly scratchVec = new THREE.Vector3();

  // Internal state
  private robotLayout: any = {};
  private jointAngles: Record<string, number> = {};
  private selectedLegKey: string = 'left_rear';
  private currentHoveredJoint: 'coxa' | 'femur' | 'tibia' | null = null;
  private calibrationData: Record<string, any> = {};

  // Raycasting
  private raycaster = new THREE.Raycaster();
  private mouse = new THREE.Vector2(-999, -999);
  private readonly CAMERA_STORAGE_KEY = 'lasius_camera_state';
  private cameraSaveTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(containers: GraphicsContainers, callbacks: GraphicsCallbacks) {
    this.containers = containers;
    this.callbacks = callbacks;

    this.init2DCanvases();
    this.initThreeJS();
    this.initMaterials();
    this.setupEvents();
    this.loadFreeCADV2Meshes();
  }

  private init2DCanvases() {
    this.topCtx = this.containers.topCanvas.getContext('2d')!;
    this.sideCtx = this.containers.sideCanvas.getContext('2d')!;
    this.frontCtx = this.containers.frontCanvas.getContext('2d')!;
    this.syncCanvasDimensions();
  }

  private syncCanvasDimensions() {
    for (const canvas of [this.containers.topCanvas, this.containers.sideCanvas, this.containers.frontCanvas]) {
      const rect = canvas.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        const w = Math.round(rect.width);
        const h = Math.round(rect.height);
        if (canvas.width !== w || canvas.height !== h) {
          canvas.width = w;
          canvas.height = h;
        }
      }
    }
  }

  private initThreeJS() {
    const el = this.containers.threeContainer;
    const width = el.clientWidth || 820;
    const height = el.clientHeight || 520;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a24);

    this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
    this.camera.position.set(380, 280, 380);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    el.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, -15, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.15;
    this.controls.minDistance = 80;
    this.controls.maxDistance = 1200;

    this.restoreCameraState();
    this.controls.addEventListener('change', () => {
      if (this.cameraSaveTimer) clearTimeout(this.cameraSaveTimer);
      this.cameraSaveTimer = setTimeout(() => this.saveCameraState(), 150);
    });

    // Ground Grid Group at y = -80 (supports kinematic stance propulsion & yaw rotation)
    this.groundGridGroup = new THREE.Group();
    this.groundGridGroup.position.set(0, -80, 0);
    this.groundGrid = new THREE.GridHelper(1400, 70, 0x323446, 0x323446);
    this.groundGridGroup.add(this.groundGrid);
    this.scene.add(this.groundGridGroup);

    // Robot Root Group (tilts & elevates with ground contact in Ground Lock mode)
    this.robotRootGroup = new THREE.Group();
    this.scene.add(this.robotRootGroup);

    // Orientation Gizmo at (0, -80, 0)
    const axes = new THREE.AxesHelper(60);
    axes.position.set(0, -80, 0);
    this.scene.add(axes);

    // Lights
    const ambLight = new THREE.AmbientLight(0xffffff, 0.75);
    this.scene.add(ambLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.95);
    dirLight1.position.set(220, 420, 220);
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x7090b0, 0.45);
    dirLight2.position.set(-220, 220, -220);
    this.scene.add(dirLight2);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.38);
    rimLight.position.set(0, -200, 300);
    this.scene.add(rimLight);

    this.animate();
  }

  private animate = () => {
    this.animFrameId = requestAnimationFrame(this.animate);
    if (this.controls) this.controls.update();
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  };

  private initMaterials() {
    this.legNeutralMat = new THREE.MeshStandardMaterial({
      color: 0x343848,
      roughness: 0.42,
      metalness: 0.35,
      side: THREE.DoubleSide
    });
    this.chassisMat = new THREE.MeshStandardMaterial({
      color: 0x2f3342,
      roughness: 0.44,
      metalness: 0.36,
      side: THREE.DoubleSide
    });
    this.coverNeutralMat = new THREE.MeshStandardMaterial({
      color: 0x242734,
      roughness: 0.40,
      metalness: 0.38,
      side: THREE.DoubleSide
    });
    this.canopyMat = this.coverNeutralMat;
    this.tarsusNeutralMat = this.legNeutralMat;
    this.kufeNeutralMat = this.legNeutralMat;
    this.pcbGreenMat = new THREE.MeshStandardMaterial({
      color: 0x14853d,
      roughness: 0.45,
      metalness: 0.25,
      side: THREE.DoubleSide
    });
    this.pcbRedMat = new THREE.MeshStandardMaterial({
      color: 0xbf2626,
      roughness: 0.45,
      metalness: 0.25,
      side: THREE.DoubleSide
    });
    this.eyeMat = new THREE.MeshStandardMaterial({
      color: 0x00d2d3,
      emissive: 0x00d2d3,
      emissiveIntensity: 0.9,
      roughness: 0.2
    });

    this.hardwareMat = new THREE.MeshStandardMaterial({
      color: 0x1a1c26,
      roughness: 0.52,
      metalness: 0.32,
      side: THREE.DoubleSide
    });
    this.carbonPlateMat = new THREE.MeshStandardMaterial({
      color: 0x1c1d26,
      roughness: 0.38,
      metalness: 0.40,
      side: THREE.DoubleSide
    });
    this.brassMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      roughness: 0.35,
      metalness: 0.75,
      side: THREE.DoubleSide
    });
    this.aluSpacerMat = new THREE.MeshStandardMaterial({
      color: 0xc4c9d4,
      roughness: 0.28,
      metalness: 0.85,
      side: THREE.DoubleSide
    });
    this.bearingMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      roughness: 0.18,
      metalness: 0.92,
      side: THREE.DoubleSide
    });

    this.chassisAxisMat = new THREE.MeshStandardMaterial({
      color: 0xd0d4de,
      roughness: 0.3,
      metalness: 0.65
    });
    this.chassisMountActiveMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.6,
      roughness: 0.25,
      metalness: 0.5
    });

    this.jointNeutralMat = new THREE.MeshStandardMaterial({
      color: 0x222532,
      roughness: 0.48,
      metalness: 0.42,
      side: THREE.DoubleSide
    });

    this.legSelectedMat = new THREE.MeshStandardMaterial({
      color: 0x2980b9,
      roughness: 0.32,
      metalness: 0.35,
      emissive: 0x0d3b66,
      emissiveIntensity: 0.45,
      side: THREE.DoubleSide
    });
    this.jointSelectedMat = new THREE.MeshStandardMaterial({
      color: 0x1f5f8b,
      roughness: 0.35,
      metalness: 0.55,
      emissive: 0x092540,
      emissiveIntensity: 0.40,
      side: THREE.DoubleSide
    });

    this.legActiveSegmentMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      roughness: 0.20,
      metalness: 0.45,
      emissive: 0x0284c7,
      emissiveIntensity: 0.85,
      side: THREE.DoubleSide
    });
    this.jointActiveMat = new THREE.MeshStandardMaterial({
      color: 0x67e8f9,
      roughness: 0.25,
      metalness: 0.60,
      emissive: 0x0ea5e9,
      emissiveIntensity: 0.90,
      side: THREE.DoubleSide
    });

    this.axisGuideMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.95
    });
  }

  /**
   * Asynchronously loads the 29 canonical FreeCAD v2 Binary STL meshes from `/meshes/*.stl`
   * and transforms them into their exact Three.js link-local millimeter coordinate frames.
   */
  private loadFreeCADV2Meshes() {
    if (this.stlLoadingStarted || typeof window === 'undefined') return;
    this.stlLoadingStarted = true;

    const loader = new STLLoader();

    // 1. Chassis transform: (X_three, Y_three, Z_three) = (-1000 * y_m, 1000 * z_m - 17.25, -1000 * x_m)
    const matBody = new THREE.Matrix4().set(
      0, -1000, 0, 0,
      0, 0, 1000, -CHASSIS_SPECS.hipPivotZ_FC,
      -1000, 0, 0, 0,
      0, 0, 0, 1
    );

    // 2. Coxa transform: (X_coxa, Y_coxa, Z_coxa) = (1000 * (60/56.5) * x_m, 1000 * z_m, -1000 * y_m)
    const coxaScaleX = COXA_SPECS.kinematicLength / COXA_SPECS.cadKinematicLength;
    const matCoxa = new THREE.Matrix4().set(
      1000 * coxaScaleX, 0, 0, 0,
      0, 0, 1000, 0,
      0, -1000, 0, 0,
      0, 0, 0, 1
    );

    // 3. Femur transform: (X_femur, Y_femur, Z_femur) = (1000 * x_m, 1000 * z_m, -1000 * y_m ± 2.50)
    const matFemurLeft = new THREE.Matrix4().set(
      1000, 0, 0, 0,
      0, 0, 1000, 0,
      0, -1000, 0, 2.50,
      0, 0, 0, 1
    );
    const matFemurRight = new THREE.Matrix4().set(
      1000, 0, 0, 0,
      0, 0, 1000, 0,
      0, -1000, 0, -2.50,
      0, 0, 0, 1
    );

    // 4. Tibia + Tarsus + Compact Kufe transform:
    //    Maps Knee (0,0,0) -> (0,0,0) and Kufe Sole (0.1522, ±0.0025, 0.01045) -> (0, -152.56, 0)
    const dxSole = 152.20;
    const dzSole = 10.45;
    const lEff = Math.hypot(dxSole, dzSole);
    const cosA = dxSole / lEff;
    const sinA = dzSole / lEff;

    const matTibiaLeft = new THREE.Matrix4().set(
      -1000 * sinA, 0, 1000 * cosA, 0,
      -1000 * cosA, 0, -1000 * sinA, 0,
      0, -1000, 0, 2.50,
      0, 0, 0, 1
    );
    const matTibiaRight = new THREE.Matrix4().set(
      -1000 * sinA, 0, 1000 * cosA, 0,
      -1000 * cosA, 0, -1000 * sinA, 0,
      0, -1000, 0, -2.50,
      0, 0, 0, 1
    );

    const specs: Array<{ key: string; file: string; matrix: THREE.Matrix4 }> = [
      // Chassis v2 (9 parts)
      { key: 'body_bottom', file: 'body_bottom.stl', matrix: matBody },
      { key: 'body_top', file: 'body_top.stl', matrix: matBody },
      { key: 'chassis_core', file: 'chassis_core.stl', matrix: matBody },
      { key: 'chassis_belly_pan', file: 'chassis_belly_pan.stl', matrix: matBody },
      { key: 'chassis_battery_hatch', file: 'chassis_battery_hatch.stl', matrix: matBody },
      { key: 'chassis_rpi_mount', file: 'chassis_rpi_mount.stl', matrix: matBody },
      { key: 'chassis_canopy', file: 'chassis_canopy.stl', matrix: matBody },
      { key: 'chassis_service_cover', file: 'chassis_service_cover.stl', matrix: matBody },
      { key: 'rpi4_model_b', file: 'rpi4_model_b.stl', matrix: matBody },
      { key: 'vl53l5cx_board', file: 'vl53l5cx_board.stl', matrix: matBody },
      // Coxa v2 (Left & Right)
      { key: 'coxa_left', file: 'coxa_left.stl', matrix: matCoxa },
      { key: 'coxa_right', file: 'coxa_right.stl', matrix: matCoxa },
      { key: 'coxa_servo_left', file: 'coxa_servo_left.stl', matrix: matCoxa },
      { key: 'coxa_servo_right', file: 'coxa_servo_right.stl', matrix: matCoxa },
      { key: 'femur_servo_left', file: 'femur_servo_left.stl', matrix: matCoxa },
      { key: 'femur_servo_right', file: 'femur_servo_right.stl', matrix: matCoxa },
      // Femur v2 (Left & Right)
      { key: 'femur_left', file: 'femur_left.stl', matrix: matFemurLeft },
      { key: 'femur_right', file: 'femur_right.stl', matrix: matFemurRight },
      { key: 'femur_cover_left', file: 'femur_cover_left.stl', matrix: matFemurLeft },
      { key: 'femur_cover_right', file: 'femur_cover_right.stl', matrix: matFemurRight },
      // Tibia + Tarsus + Kufe v2 (Left & Right)
      { key: 'tibia_left', file: 'tibia_left.stl', matrix: matTibiaLeft },
      { key: 'tibia_right', file: 'tibia_right.stl', matrix: matTibiaRight },
      { key: 'tibia_cover_left', file: 'tibia_cover_left.stl', matrix: matTibiaLeft },
      { key: 'tibia_cover_right', file: 'tibia_cover_right.stl', matrix: matTibiaRight },
      { key: 'knee_servo_left', file: 'knee_servo_left.stl', matrix: matTibiaLeft },
      { key: 'knee_servo_right', file: 'knee_servo_right.stl', matrix: matTibiaRight },
      { key: 'tarsus_left', file: 'tarsus_left.stl', matrix: matTibiaLeft },
      { key: 'tarsus_right', file: 'tarsus_right.stl', matrix: matTibiaRight },
      { key: 'tarsus_shoe_left', file: 'tarsus_shoe_left.stl', matrix: matTibiaLeft },
      { key: 'tarsus_shoe_right', file: 'tarsus_shoe_right.stl', matrix: matTibiaRight }
    ];

    let settledCount = 0;
    const totalCount = specs.length;

    const loadItem = (item: { key: string; file: string; matrix: THREE.Matrix4 }, attempt = 1) => {
      loader.load(
        `./meshes/${item.file}`,
        (geom) => {
          geom.applyMatrix4(item.matrix);
          geom.computeVertexNormals();
          this.stlGeometries[item.key] = geom;
          settledCount++;
          if (settledCount === totalCount) {
            this.stlLoadedReady = Object.keys(this.stlGeometries).length > 0;
            if (this.robotLayout && this.robotLayout.legs) {
              this.buildThreeJSRobot(this.robotLayout);
            }
          }
        },
        undefined,
        () => {
          if (attempt < 3) {
            setTimeout(() => loadItem(item, attempt + 1), 150 * attempt);
          } else {
            settledCount++;
            if (settledCount === totalCount) {
              this.stlLoadedReady = Object.keys(this.stlGeometries).length > 0;
              if (this.robotLayout && this.robotLayout.legs) {
                this.buildThreeJSRobot(this.robotLayout);
              }
            }
          }
        }
      );
    };

    for (const item of specs) {
      loadItem(item);
    }
  }

  public getChassisHullContour(): Array<{ x: number; y: number }> {
    return CHASSIS_HULL_CONTOUR;
  }

  private disposeObject3D(obj: THREE.Object3D | null | undefined) {
    if (!obj) return;
    const cachedGeos = new Set<THREE.BufferGeometry>(Object.values(this.stlGeometries));

    obj.traverse((child: any) => {
      if (child.geometry && typeof child.geometry.dispose === 'function' && !cachedGeos.has(child.geometry)) {
        child.geometry.dispose();
      }
    });
  }

  private updateFanGeometry(geometry: THREE.BufferGeometry, fanPositions: number[]) {
    const existing = geometry.getAttribute('position') as THREE.BufferAttribute | undefined;
    if (existing && existing.array.length === fanPositions.length) {
      (existing.array as Float32Array).set(fanPositions);
      existing.needsUpdate = true;
    } else {
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(fanPositions, 3));
    }
    geometry.computeVertexNormals();
  }

  public buildThreeJSRobot(layout: any) {
    if (!this.scene || !layout || !layout.body || !layout.legs) return;
    this.robotLayout = layout;

    // Wait for canonical FreeCAD v2 STL meshes before constructing the 3D scene
    // so there is no visual swap from a temporary procedural placeholder model.
    if (!this.stlLoadedReady) {
      this.drawRobot();
      return;
    }

    if (this.robot3DMeshes.body) {
      this.disposeObject3D(this.robot3DMeshes.body);
      this.robotRootGroup.remove(this.robot3DMeshes.body);
    }
    if (this.robot3DMeshes.axesGroup) {
      this.disposeObject3D(this.robot3DMeshes.axesGroup);
      this.robotRootGroup.remove(this.robot3DMeshes.axesGroup);
    }
    if (this.robot3DMeshes.arcsGroup) {
      this.disposeObject3D(this.robot3DMeshes.arcsGroup);
      this.robotRootGroup.remove(this.robot3DMeshes.arcsGroup);
    }
    if (this.robot3DMeshes.trailsGroup) {
      this.disposeObject3D(this.robot3DMeshes.trailsGroup);
      this.scene.remove(this.robot3DMeshes.trailsGroup);
    }
    this.robot3DMeshes.axesGroup = null;
    this.robot3DMeshes.axes = null;
    this.robot3DMeshes.arcsGroup = null;
    this.robot3DMeshes.trailsGroup = null;
    this.robot3DMeshes.contactRings = {};
    this.robot3DMeshes.trailLines = {};
    this.footTrailHistory = {};

    for (const legName in this.robot3DMeshes.legs) {
      const g = this.robot3DMeshes.legs[legName];
      if (g.coxaGroup) {
        this.disposeObject3D(g.coxaGroup);
        this.robotRootGroup.remove(g.coxaGroup);
      }
      if (g.femurGroup) {
        this.disposeObject3D(g.femurGroup);
        this.robotRootGroup.remove(g.femurGroup);
      }
      if (g.tibiaGroup) {
        this.disposeObject3D(g.tibiaGroup);
        this.robotRootGroup.remove(g.tibiaGroup);
      }
    }
    this.robot3DMeshes.legs = {};

    // 1. Build v2 Chassis Assembly (`body_assembly.FCStd`)
    const bodyGroup = new THREE.Group();

    const chassisParts: Array<{ key: string; mat: THREE.Material; renderOrder?: number }> = [
      { key: 'body_bottom', mat: this.carbonPlateMat },
      { key: 'body_top', mat: this.carbonPlateMat },
      { key: 'chassis_core', mat: this.chassisMat },
      { key: 'chassis_belly_pan', mat: this.hardwareMat },
      { key: 'chassis_battery_hatch', mat: this.hardwareMat },
      { key: 'chassis_rpi_mount', mat: this.chassisMat },
      { key: 'rpi4_model_b', mat: this.pcbGreenMat },
      { key: 'vl53l5cx_board', mat: this.pcbRedMat },
      { key: 'chassis_service_cover', mat: this.coverNeutralMat },
      { key: 'chassis_canopy', mat: this.canopyMat, renderOrder: 10 }
    ];
    for (const part of chassisParts) {
      const geo = this.stlGeometries[part.key];
      if (geo) {
        const mesh = new THREE.Mesh(geo, part.mat);
        if (part.renderOrder !== undefined) {
          mesh.renderOrder = part.renderOrder;
        }
        bodyGroup.add(mesh);
      }
    }

    // Front Direction Indicator (Blue Triangle on Top Plate pointing forward -Z)
    const triangleShape = new THREE.Shape();
    triangleShape.moveTo(0, -118);
    triangleShape.lineTo(7, -98);
    triangleShape.lineTo(-7, -98);
    triangleShape.closePath();

    const triangleGeo = new THREE.ExtrudeGeometry(triangleShape, {
      depth: 1.0,
      bevelEnabled: true,
      bevelSegments: 1,
      steps: 1,
      bevelSize: 0.2,
      bevelThickness: 0.2
    });
    triangleGeo.translate(0, 0, -0.5);
    triangleGeo.rotateX(Math.PI / 2);

    const triangleMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.7,
      roughness: 0.3,
      metalness: 0.2
    });
    const triangleMesh = new THREE.Mesh(triangleGeo, triangleMat);
    triangleMesh.position.set(0, CHASSIS_SPECS.topPlateCenterY + CHASSIS_SPECS.plateThickness / 2 + 0.8, 0);
    bodyGroup.add(triangleMesh);

    this.robotRootGroup.add(bodyGroup);
    this.robot3DMeshes.body = bodyGroup;

    // 2. Build Six Modular v2 Legs
    for (const legName in layout.legs) {
      const isRightLeg = legName.startsWith('right_');
      const coxaGroup = this.createCoxaGroup(isRightLeg);
      const femurGroup = this.createFemurGroup(isRightLeg);
      const tibiaLen = layout.legs[legName]?.tibia?.length ?? TIBIA_SPECS.kinematicLength;
      const tibiaGroup = this.createTibiaGroup(tibiaLen, isRightLeg);

      [coxaGroup, femurGroup, tibiaGroup].forEach(g => {
        g.traverse(child => {
          if ((child as THREE.Mesh).isMesh) {
            child.userData.legName = legName;
          }
        });
      });

      this.robotRootGroup.add(coxaGroup);
      this.robotRootGroup.add(femurGroup);
      this.robotRootGroup.add(tibiaGroup);

      this.robot3DMeshes.legs[legName] = { coxaGroup, femurGroup, tibiaGroup };
    }

    this.initAxisGuideObjects();
    this.initMotionRangeArcObjects();
    this.initFootTrailsAndContacts();
    this.update3DLegHighlights();
    this.drawRobot();
  }

  private initFootTrailsAndContacts() {
    if (this.robot3DMeshes.trailsGroup || !this.robotLayout.legs) return;

    const trailsGroup = new THREE.Group();
    trailsGroup.visible = this.showFootTrails;

    const ringGeo = new THREE.RingGeometry(4.5, 8.5, 24);
    ringGeo.rotateX(-Math.PI / 2);

    for (const legName in this.robotLayout.legs) {
      // 1. Ground contact ring at y = -79.6
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x2ecc71,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.75,
        depthWrite: false
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.position.set(0, -79.6, 0);
      ringMesh.visible = false;
      trailsGroup.add(ringMesh);
      this.robot3DMeshes.contactRings[legName] = ringMesh;

      // 2. 3D Foot Trajectory Trail line
      const trailMat = new THREE.LineBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.65
      });
      const trailGeo = new THREE.BufferGeometry();
      const trailLine = new THREE.Line(trailGeo, trailMat);
      trailsGroup.add(trailLine);
      this.robot3DMeshes.trailLines[legName] = trailLine;
      this.footTrailHistory[legName] = [];
    }

    this.scene.add(trailsGroup);
    this.robot3DMeshes.trailsGroup = trailsGroup;
  }

  public setShowFootTrails(visible: boolean) {
    this.showFootTrails = visible;
    if (this.robot3DMeshes.trailsGroup) {
      this.robot3DMeshes.trailsGroup.visible = visible;
    }
    if (!visible) {
      for (const k in this.footTrailHistory) {
        this.footTrailHistory[k] = [];
      }
    }
  }

  public setGroundLocked(locked: boolean) {
    this.groundLocked = locked;
    if (!locked) {
      this.chassisWorldZ = 0.0;
      this.chassisWorldQuat.identity();
      if (this.robotRootGroup) {
        this.robotRootGroup.position.set(0, 0, 0);
        this.robotRootGroup.quaternion.identity();
      }
      if (this.groundGridGroup && this.groundGrid) {
        this.groundYaw = 0.0;
        this.groundLocalX = 0.0;
        this.groundLocalZ = 0.0;
        this.groundGridGroup.rotation.y = 0.0;
        this.groundGrid.position.set(0, 0, 0);
      }
    }
    this.drawRobot();
  }

  private createCoxaGroup(isRightLeg = false): THREE.Group {
    const group = new THREE.Group();
    const side = isRightLeg ? 'right' : 'left';

    let bracket: THREE.Mesh | null = null;
    if (this.stlGeometries[`coxa_${side}`]) {
      bracket = new THREE.Mesh(this.stlGeometries[`coxa_${side}`], this.legNeutralMat);
      bracket.userData = { jointType: 'coxa' };
      group.add(bracket);
    }

    const servos: THREE.Mesh[] = [];
    for (const sKey of [`coxa_servo_${side}`, `femur_servo_${side}`]) {
      if (this.stlGeometries[sKey]) {
        const sm = new THREE.Mesh(this.stlGeometries[sKey], this.hardwareMat);
        sm.userData = { jointType: 'coxa' };
        group.add(sm);
        servos.push(sm);
      }
    }

    group.userData = { bracket, servoBox: servos[0] || null, extraServos: servos, isStlV2: true };
    return group;
  }

  private createFemurGroup(isRightLeg = false): THREE.Group {
    const group = new THREE.Group();
    const side = isRightLeg ? 'right' : 'left';

    const plates: THREE.Mesh[] = [];
    if (this.stlGeometries[`femur_${side}`]) {
      const bodyMesh = new THREE.Mesh(this.stlGeometries[`femur_${side}`], this.legNeutralMat);
      bodyMesh.userData = { jointType: 'femur' };
      group.add(bodyMesh);
      plates.push(bodyMesh);
    }

    const covers: THREE.Mesh[] = [];
    if (this.stlGeometries[`femur_cover_${side}`]) {
      const coverMesh = new THREE.Mesh(this.stlGeometries[`femur_cover_${side}`], this.coverNeutralMat);
      coverMesh.userData = { jointType: 'femur' };
      group.add(coverMesh);
      covers.push(coverMesh);
    }

    group.userData = { plates, rungs: covers, isStlV2: true };
    return group;
  }

  private createTibiaGroup(tibiaLen = TIBIA_SPECS.kinematicLength, isRightLeg = false): THREE.Group {
    const group = new THREE.Group();
    const side = isRightLeg ? 'right' : 'left';
    const lenScale = tibiaLen / TIBIA_SPECS.kinematicLength;

    let blade: THREE.Mesh | null = null;
    if (this.stlGeometries[`tibia_${side}`]) {
      blade = new THREE.Mesh(this.stlGeometries[`tibia_${side}`], this.legNeutralMat);
      blade.scale.set(1.0, lenScale, 1.0);
      blade.userData = { jointType: 'tibia' };
      group.add(blade);
    }

    let coverMesh: THREE.Mesh | null = null;
    if (this.stlGeometries[`tibia_cover_${side}`]) {
      coverMesh = new THREE.Mesh(this.stlGeometries[`tibia_cover_${side}`], this.coverNeutralMat);
      coverMesh.scale.set(1.0, lenScale, 1.0);
      coverMesh.userData = { jointType: 'tibia' };
      group.add(coverMesh);
    }

    let clamp: THREE.Mesh | null = null;
    if (this.stlGeometries[`knee_servo_${side}`]) {
      clamp = new THREE.Mesh(this.stlGeometries[`knee_servo_${side}`], this.hardwareMat);
      clamp.userData = { jointType: 'tibia' };
      group.add(clamp);
    }

    let tarsusMesh: THREE.Mesh | null = null;
    if (this.stlGeometries[`tarsus_${side}`]) {
      tarsusMesh = new THREE.Mesh(this.stlGeometries[`tarsus_${side}`], this.tarsusNeutralMat);
      tarsusMesh.scale.set(1.0, lenScale, 1.0);
      tarsusMesh.userData = { jointType: 'tibia' };
      group.add(tarsusMesh);
    }

    let shoeMesh: THREE.Mesh | null = null;
    if (this.stlGeometries[`tarsus_shoe_${side}`]) {
      shoeMesh = new THREE.Mesh(this.stlGeometries[`tarsus_shoe_${side}`], this.kufeNeutralMat);
      shoeMesh.scale.set(1.0, lenScale, 1.0);
      shoeMesh.userData = { jointType: 'tibia' };
      group.add(shoeMesh);
    }

    group.userData = { blade, coverMesh, clamp, tarsusMesh, shoeMesh, isStlV2: true };
    return group;
  }

  private initAxisGuideObjects() {
    if (this.robot3DMeshes.axesGroup) return;

    const axisEndCapGeo = new THREE.SphereGeometry(1.6, 12, 12);
    const coxaCylGeo = new THREE.CylinderGeometry(0.85, 0.85, 54, 16);
    const pitchCylGeo = new THREE.CylinderGeometry(0.85, 0.85, 46, 16);

    const axesGroup = new THREE.Group();
    axesGroup.renderOrder = 999;

    // 1. Coxa vertical rotation axis
    const coxaAxisGroup = new THREE.Group();
    const coxaCyl = new THREE.Mesh(coxaCylGeo, this.axisGuideMat);
    const coxaCapTop = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    coxaCapTop.position.set(0, 27, 0);
    const coxaCapBottom = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    coxaCapBottom.position.set(0, -27, 0);
    coxaAxisGroup.add(coxaCyl, coxaCapTop, coxaCapBottom);
    axesGroup.add(coxaAxisGroup);

    // 2. Femur pitch rotation axis (local Z)
    const femurAxisGroup = new THREE.Group();
    const femurCyl = new THREE.Mesh(pitchCylGeo, this.axisGuideMat);
    femurCyl.rotateX(Math.PI / 2);
    const femurCap1 = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    femurCap1.position.set(0, 0, 23);
    const femurCap2 = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    femurCap2.position.set(0, 0, -23);
    femurAxisGroup.add(femurCyl, femurCap1, femurCap2);
    axesGroup.add(femurAxisGroup);

    // 3. Tibia knee pitch rotation axis (local Z)
    const tibiaAxisGroup = new THREE.Group();
    const tibiaCyl = new THREE.Mesh(pitchCylGeo, this.axisGuideMat);
    tibiaCyl.rotateX(Math.PI / 2);
    const tibiaCap1 = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    tibiaCap1.position.set(0, 0, 23);
    const tibiaCap2 = new THREE.Mesh(axisEndCapGeo, this.axisGuideMat);
    tibiaCap2.position.set(0, 0, -23);
    tibiaAxisGroup.add(tibiaCyl, tibiaCap1, tibiaCap2);
    axesGroup.add(tibiaAxisGroup);

    this.robotRootGroup.add(axesGroup);
    this.robot3DMeshes.axesGroup = axesGroup;
    this.robot3DMeshes.axes = { coxa: coxaAxisGroup, femur: femurAxisGroup, tibia: tibiaAxisGroup };
  }

  private updateAxisGuideLines(v0: THREE.Vector3, v1: THREE.Vector3, v2: THREE.Vector3, normal: THREE.Vector3) {
    if (!this.robot3DMeshes.axes) return;
    const { coxa, femur, tibia } = this.robot3DMeshes.axes;
    coxa.position.copy(v0);
    femur.position.copy(v1);
    femur.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
    tibia.position.copy(v2);
    tibia.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
  }

  private initMotionRangeArcObjects() {
    if (this.robot3DMeshes.arcsGroup) return;

    const createSingleArc = () => {
      const group = new THREE.Group();
      group.visible = false;

      const lineMat = new THREE.LineBasicMaterial({
        color: 0x38bdf8,
        linewidth: 2,
        transparent: true,
        opacity: 0.85,
        depthTest: false
      });

      const fanMat = new THREE.MeshBasicMaterial({
        color: 0x0284c7,
        transparent: true,
        opacity: 0.14,
        side: THREE.DoubleSide,
        depthTest: false,
        depthWrite: false
      });

      const needleMat = new THREE.LineBasicMaterial({
        color: 0x67e8f9,
        linewidth: 2,
        depthTest: false
      });

      const beadMeshMat = new THREE.MeshBasicMaterial({
        color: 0x67e8f9,
        depthTest: false
      });

      const lineGeo = new THREE.BufferGeometry();
      const arcLine = new THREE.Line(lineGeo, lineMat);

      const ticksGeo = new THREE.BufferGeometry();
      const ticksLine = new THREE.LineSegments(ticksGeo, lineMat);

      const fanGeo = new THREE.BufferGeometry();
      const fanMesh = new THREE.Mesh(fanGeo, fanMat);

      const needleGeo = new THREE.BufferGeometry();
      const needle = new THREE.Line(needleGeo, needleMat);

      const beadGeo = new THREE.SphereGeometry(2.4, 12, 12);
      const bead = new THREE.Mesh(beadGeo, beadMeshMat);

      group.add(fanMesh, arcLine, ticksLine, needle, bead);
      group.renderOrder = 1000;
      return { group, arcLine, ticksLine, fanMesh, needle, bead, lineMat, fanMat, beadMeshMat };
    };

    const arcsGroup = new THREE.Group();
    const coxa = createSingleArc();
    const femur = createSingleArc();
    const tibia = createSingleArc();

    arcsGroup.add(coxa.group, femur.group, tibia.group);
    this.robotRootGroup.add(arcsGroup);

    this.robot3DMeshes.arcsGroup = arcsGroup;
    this.motionRangeArcs = { coxa, femur, tibia };
  }

  private getJointLimits(sName: string, jointType: 'coxa' | 'femur' | 'tibia') {
    const sData = this.calibrationData[sName] || {};
    const defaultMin = jointType === 'tibia' ? -68 : (jointType === 'coxa' ? -25 : -90);
    const defaultMax = jointType === 'tibia' ? 29 : (jointType === 'coxa' ? (sName.includes('front') ? 35 : 25) : 90);
    return {
      minAngle: sData.min_angle !== undefined ? sData.min_angle : defaultMin,
      maxAngle: sData.max_angle !== undefined ? sData.max_angle : defaultMax
    };
  }

  public updateMotionRangeArcs() {
    if (!this.motionRangeArcs || !this.motionRangeArcs.coxa || !this.lastSelectedLegKinematics) return;
    const { coxa, femur, tibia } = this.motionRangeArcs;

    const hasActiveLeg = Boolean(this.selectedLegKey && this.robotLayout.legs && this.robotLayout.legs[this.selectedLegKey]);
    coxa.group.visible = hasActiveLeg;
    femur.group.visible = hasActiveLeg;
    tibia.group.visible = hasActiveLeg;

    if (!hasActiveLeg) return;

    const { v0, v1, v2, normal, totalAngle, baseAngle } = this.lastSelectedLegKinematics;
    const legKey = this.selectedLegKey;
    const legDef = this.robotLayout.legs[legKey];
    if (!legDef) return;

    const names = {
      coxa: legDef.coxa.name,
      femur: legDef.femur.name,
      tibia: legDef.tibia.name
    };

    const rVec = new THREE.Vector3(Math.cos(totalAngle), 0, Math.sin(totalAngle)).normalize();
    const upVec = new THREE.Vector3(0, 1, 0);
    const segments = 32;

    // --- 1. COXA ARC (Horizontal plane at v0) ---
    {
      const isHovered = (this.currentHoveredJoint === 'coxa');
      coxa.lineMat.color.setHex(isHovered ? 0x67e8f9 : 0x38bdf8);
      coxa.lineMat.opacity = isHovered ? 1.0 : 0.85;
      coxa.fanMat.opacity = isHovered ? 0.28 : 0.14;
      coxa.beadMeshMat.color.setHex(isHovered ? 0xa5f3fc : 0x67e8f9);
      coxa.bead.scale.setScalar(isHovered ? 1.35 : 1.0);

      const sName = names.coxa;
      const limits = this.getJointLimits(sName, 'coxa');
      const minRad = limits.minAngle * Math.PI / 180;
      const maxRad = limits.maxAngle * Math.PI / 180;
      const curDeg = this.jointAngles[sName] || 0;
      const curRad = curDeg * Math.PI / 180;
      const R = 38;

      const pts: THREE.Vector3[] = [];
      const fanPositions: number[] = [];
      for (let i = 0; i <= segments; i++) {
        const frac = i / segments;
        const a = baseAngle + minRad + frac * (maxRad - minRad);
        const p = new THREE.Vector3(v0.x + R * Math.cos(a), v0.y + 1.2, v0.z + R * Math.sin(a));
        pts.push(p);
      }
      for (let i = 0; i < segments; i++) {
        fanPositions.push(v0.x, v0.y + 1.0, v0.z);
        fanPositions.push(pts[i].x, pts[i].y, pts[i].z);
        fanPositions.push(pts[i + 1].x, pts[i + 1].y, pts[i + 1].z);
      }

      coxa.arcLine.geometry.setFromPoints(pts);
      this.updateFanGeometry(coxa.fanMesh.geometry, fanPositions);

      const tickPts: THREE.Vector3[] = [];
      [minRad, 0, maxRad].forEach(offset => {
        const a = baseAngle + offset;
        tickPts.push(
          new THREE.Vector3(v0.x + (R - 5) * Math.cos(a), v0.y + 1.2, v0.z + (R - 5) * Math.sin(a)),
          new THREE.Vector3(v0.x + (R + 5) * Math.cos(a), v0.y + 1.2, v0.z + (R + 5) * Math.sin(a))
        );
      });
      coxa.ticksLine.geometry.setFromPoints(tickPts);

      const liveA = baseAngle + curRad;
      const curPos = new THREE.Vector3(v0.x + R * Math.cos(liveA), v0.y + 1.4, v0.z + R * Math.sin(liveA));
      coxa.needle.geometry.setFromPoints([new THREE.Vector3(v0.x, v0.y + 1.2, v0.z), curPos]);
      coxa.bead.position.copy(curPos);
    }

    // --- 2. FEMUR ARC (Vertical bending plane at v1) ---
    {
      const isHovered = (this.currentHoveredJoint === 'femur');
      femur.lineMat.color.setHex(isHovered ? 0x67e8f9 : 0x38bdf8);
      femur.lineMat.opacity = isHovered ? 1.0 : 0.85;
      femur.fanMat.opacity = isHovered ? 0.28 : 0.14;
      femur.beadMeshMat.color.setHex(isHovered ? 0xa5f3fc : 0x67e8f9);
      femur.bead.scale.setScalar(isHovered ? 1.35 : 1.0);

      const sName = names.femur;
      const limits = this.getJointLimits(sName, 'femur');
      const minRad = limits.minAngle * Math.PI / 180;
      const maxRad = limits.maxAngle * Math.PI / 180;
      const curDeg = this.jointAngles[sName] || 0;
      const curRad = curDeg * Math.PI / 180;
      const R = 42;

      const pts: THREE.Vector3[] = [];
      const fanPositions: number[] = [];
      for (let i = 0; i <= segments; i++) {
        const frac = i / segments;
        const a = minRad + frac * (maxRad - minRad);
        const p = new THREE.Vector3()
          .copy(v1)
          .addScaledVector(rVec, R * Math.cos(a))
          .addScaledVector(upVec, R * Math.sin(a));
        pts.push(p);
      }
      for (let i = 0; i < segments; i++) {
        fanPositions.push(v1.x, v1.y, v1.z);
        fanPositions.push(pts[i].x, pts[i].y, pts[i].z);
        fanPositions.push(pts[i + 1].x, pts[i + 1].y, pts[i + 1].z);
      }

      femur.arcLine.geometry.setFromPoints(pts);
      this.updateFanGeometry(femur.fanMesh.geometry, fanPositions);

      const tickPts: THREE.Vector3[] = [];
      [minRad, 0, maxRad].forEach(offset => {
        const pInner = new THREE.Vector3().copy(v1).addScaledVector(rVec, (R - 5) * Math.cos(offset)).addScaledVector(upVec, (R - 5) * Math.sin(offset));
        const pOuter = new THREE.Vector3().copy(v1).addScaledVector(rVec, (R + 5) * Math.cos(offset)).addScaledVector(upVec, (R + 5) * Math.sin(offset));
        tickPts.push(pInner, pOuter);
      });
      femur.ticksLine.geometry.setFromPoints(tickPts);

      const curPos = new THREE.Vector3().copy(v1).addScaledVector(rVec, R * Math.cos(curRad)).addScaledVector(upVec, R * Math.sin(curRad));
      femur.needle.geometry.setFromPoints([new THREE.Vector3().copy(v1), curPos]);
      femur.bead.position.copy(curPos);
    }

    // --- 3. TIBIA ARC (Knee bending plane at v2) ---
    {
      const isHovered = (this.currentHoveredJoint === 'tibia');
      tibia.lineMat.color.setHex(isHovered ? 0x67e8f9 : 0x38bdf8);
      tibia.lineMat.opacity = isHovered ? 1.0 : 0.85;
      tibia.fanMat.opacity = isHovered ? 0.28 : 0.14;
      tibia.beadMeshMat.color.setHex(isHovered ? 0xa5f3fc : 0x67e8f9);
      tibia.bead.scale.setScalar(isHovered ? 1.35 : 1.0);

      const sName = names.tibia;
      const limits = this.getJointLimits(sName, 'tibia');
      const minRad = limits.minAngle * Math.PI / 180;
      const maxRad = limits.maxAngle * Math.PI / 180;
      const curDeg = this.jointAngles[sName] || 0;
      const curRad = curDeg * Math.PI / 180;

      const femurDeg = this.jointAngles[names.femur] || 0;
      const femurRad = femurDeg * Math.PI / 180;
      const kneeCenterPitch = femurRad - Math.PI / 2;
      const R = 44;

      const pts: THREE.Vector3[] = [];
      const fanPositions: number[] = [];
      for (let i = 0; i <= segments; i++) {
        const frac = i / segments;
        const servoAngle = minRad + frac * (maxRad - minRad);
        const pitchAngle = kneeCenterPitch - servoAngle;
        const p = new THREE.Vector3()
          .copy(v2)
          .addScaledVector(rVec, R * Math.cos(pitchAngle))
          .addScaledVector(upVec, R * Math.sin(pitchAngle));
        pts.push(p);
      }
      for (let i = 0; i < segments; i++) {
        fanPositions.push(v2.x, v2.y, v2.z);
        fanPositions.push(pts[i].x, pts[i].y, pts[i].z);
        fanPositions.push(pts[i + 1].x, pts[i + 1].y, pts[i + 1].z);
      }

      tibia.arcLine.geometry.setFromPoints(pts);
      this.updateFanGeometry(tibia.fanMesh.geometry, fanPositions);

      const tickPts: THREE.Vector3[] = [];
      [minRad, 0, maxRad].forEach(offset => {
        const pitchAngle = kneeCenterPitch - offset;
        const pInner = new THREE.Vector3().copy(v2).addScaledVector(rVec, (R - 5) * Math.cos(pitchAngle)).addScaledVector(upVec, (R - 5) * Math.sin(pitchAngle));
        const pOuter = new THREE.Vector3().copy(v2).addScaledVector(rVec, (R + 5) * Math.cos(pitchAngle)).addScaledVector(upVec, (R + 5) * Math.sin(pitchAngle));
        tickPts.push(pInner, pOuter);
      });
      tibia.ticksLine.geometry.setFromPoints(tickPts);

      const livePitch = kneeCenterPitch - curRad;
      const curPos = new THREE.Vector3().copy(v2).addScaledVector(rVec, R * Math.cos(livePitch)).addScaledVector(upVec, R * Math.sin(livePitch));
      tibia.needle.geometry.setFromPoints([new THREE.Vector3().copy(v2), curPos]);
      tibia.bead.position.copy(curPos);
    }
  }

  public update3DLegHighlights(activeLegKey = this.selectedLegKey, hoveredJoint = this.currentHoveredJoint) {
    if (!this.robot3DMeshes || !this.robot3DMeshes.legs) return;

    for (const legName in this.robot3DMeshes.legs) {
      const leg = this.robot3DMeshes.legs[legName];
      if (!leg) continue;

      const isSelected = (legName === activeLegKey);
      const isCoxaActive = isSelected && (hoveredJoint === 'coxa');
      const isFemurActive = isSelected && (hoveredJoint === 'femur');
      const isTibiaActive = isSelected && (hoveredJoint === 'tibia');

      // 1. Coxa Segment
      if (leg.coxaGroup && leg.coxaGroup.userData) {
        const { bracket, servoBox, extraServos, ring1 } = leg.coxaGroup.userData;
        if (bracket) bracket.material = isSelected ? (isCoxaActive ? this.legActiveSegmentMat : this.legSelectedMat) : this.legNeutralMat;
        if (servoBox) servoBox.material = isSelected ? (isCoxaActive ? this.jointActiveMat : this.jointSelectedMat) : this.hardwareMat;
        if (Array.isArray(extraServos)) {
          const sMat = isSelected ? (isCoxaActive ? this.jointActiveMat : this.jointSelectedMat) : this.hardwareMat;
          extraServos.forEach((sm: any) => { if (sm) sm.material = sMat; });
        }
        if (ring1) ring1.material = isSelected ? ((isCoxaActive || isFemurActive) ? this.jointActiveMat : this.jointSelectedMat) : this.jointNeutralMat;
      }

      // 2. Femur Segment
      if (leg.femurGroup && leg.femurGroup.userData) {
        const { plates, rungs, kneeServo, ringHip, ringKnee } = leg.femurGroup.userData;
        if (plates) {
          const targetMat = isSelected ? (isFemurActive ? this.legActiveSegmentMat : this.legSelectedMat) : this.legNeutralMat;
          plates.forEach((p: any) => { if (p) p.material = targetMat; });
        }
        if (rungs) {
          const targetRungMat = isSelected ? (isFemurActive ? this.jointActiveMat : this.jointSelectedMat) : this.coverNeutralMat;
          rungs.forEach((r: any) => { if (r) r.material = targetRungMat; });
        }
        if (kneeServo) kneeServo.material = isSelected ? ((isFemurActive || isTibiaActive) ? this.jointActiveMat : this.jointSelectedMat) : this.hardwareMat;
        if (ringHip) ringHip.material = isSelected ? (isFemurActive ? this.jointActiveMat : this.jointSelectedMat) : this.jointNeutralMat;
        if (ringKnee) ringKnee.material = isSelected ? ((isFemurActive || isTibiaActive) ? this.jointActiveMat : this.jointSelectedMat) : this.jointNeutralMat;
      }

      // 3. Tibia + Tarsus + Compact Kufe Segment
      if (leg.tibiaGroup && leg.tibiaGroup.userData) {
        const { blade, coverMesh, clamp, tarsusMesh, shoeMesh, ringKnee } = leg.tibiaGroup.userData;
        const tibiaSegMat = isSelected ? (isTibiaActive ? this.legActiveSegmentMat : this.legSelectedMat) : this.legNeutralMat;
        if (blade) blade.material = tibiaSegMat;
        if (coverMesh) coverMesh.material = isSelected ? (isTibiaActive ? this.jointActiveMat : this.jointSelectedMat) : this.coverNeutralMat;
        if (clamp) clamp.material = isSelected ? (isTibiaActive ? this.jointActiveMat : this.jointSelectedMat) : this.hardwareMat;
        if (tarsusMesh) tarsusMesh.material = tibiaSegMat;
        if (shoeMesh) shoeMesh.material = tibiaSegMat;
        if (ringKnee) ringKnee.material = isSelected ? (isTibiaActive ? this.jointActiveMat : this.jointSelectedMat) : this.jointNeutralMat;
      }
    }
  }

  public computeLeg3D(leg: any, angles: Record<string, number>) {
    const mount = leg.mount_point;
    const baseAngle = (leg.base_angle !== undefined) ? leg.base_angle : 0;

    const coxaAngle = (angles[leg.coxa.name] || 0) * Math.PI / 180;
    const femurAngle = (angles[leg.femur.name] || 0) * Math.PI / 180;
    const tibiaServoAngle = (angles[leg.tibia.name] || 0) * Math.PI / 180;

    const totalAngle = baseAngle + coxaAngle;

    // p0: Body mount point (Z = 0)
    const p0 = { x: mount.x, y: mount.y, z: 0 };

    // p1: Coxa end / Femur start (horizontal plane)
    const p1 = {
      x: p0.x + leg.coxa.length * Math.cos(totalAngle),
      y: p0.y + leg.coxa.length * Math.sin(totalAngle),
      z: 0
    };

    // p2: Knee joint (Femur points upwards)
    const femurHoriz = leg.femur.length * Math.cos(femurAngle);
    const femurVert = leg.femur.length * Math.sin(femurAngle);

    const p2 = {
      x: p1.x + femurHoriz * Math.cos(totalAngle),
      y: p1.y + femurHoriz * Math.sin(totalAngle),
      z: p1.z + femurVert
    };

    // Tibia: knee bend angle is 90° + tibiaServoAngle
    const kneeBend = (Math.PI / 2) + tibiaServoAngle;
    const tibiaPitch = femurAngle - kneeBend;

    const tibiaHoriz = leg.tibia.length * Math.cos(tibiaPitch);
    const tibiaVert = leg.tibia.length * Math.sin(tibiaPitch);

    // p3: Foot tip
    const p3 = {
      x: p2.x + tibiaHoriz * Math.cos(totalAngle),
      y: p2.y + tibiaHoriz * Math.sin(totalAngle),
      z: p2.z + tibiaVert
    };

    return { p0, p1, p2, p3 };
  }

  private fitSupportPlane(pts: Array<{ x: number; y: number; z: number }>) {
    const n = pts.length;
    if (n === 0) return { z0: -80.0, a: 0.0, b: 0.0 };

    let mx = 0, my = 0, mz = 0;
    for (const p of pts) {
      mx += p.x;
      my += p.y;
      mz += p.z;
    }
    mx /= n;
    my /= n;
    mz /= n;

    // Regularization (lambda = 600 mm^2) guarantees stability even if < 3 feet or collinear
    const lambda = 600.0;
    let sxx = lambda, syy = lambda, sxy = 0.0, sxz = 0.0, syz = 0.0;
    for (const p of pts) {
      const dx = p.x - mx;
      const dy = p.y - my;
      const dz = p.z - mz;
      sxx += dx * dx;
      syy += dy * dy;
      sxy += dx * dy;
      sxz += dx * dz;
      syz += dy * dz;
    }

    const det = sxx * syy - sxy * sxy;
    let a = 0.0, b = 0.0;
    if (Math.abs(det) > 1e-6) {
      a = (syy * sxz - sxy * syz) / det;
      b = (sxx * syz - sxy * sxz) / det;
    }

    // Clamp max tilt slope to tan(28 deg) ~ 0.53
    const maxSlope = 0.53;
    a = Math.max(-maxSlope, Math.min(maxSlope, a));
    b = Math.max(-maxSlope, Math.min(maxSlope, b));
    const z0 = mz - a * mx - b * my;
    return { z0, a, b };
  }

  private computeWorldKinematics(legsBody: Record<string, any>): Record<string, any> {
    if (!this.groundLocked) {
      this.chassisWorldZ = 0.0;
      this.chassisWorldQuat.identity();
      if (this.robotRootGroup) {
        this.robotRootGroup.position.set(0, 0, 0);
        this.robotRootGroup.quaternion.identity();
      }
      return legsBody;
    }

    const feet: Array<{ legName: string; x: number; y: number; z: number }> = [];
    for (const legName in legsBody) {
      const p3 = legsBody[legName]?.p3;
      if (p3) {
        feet.push({ legName, x: p3.x, y: p3.y, z: p3.z });
      }
    }

    if (feet.length >= 3) {
      // Pass 1: Filter out high-lifted legs (e.g. Wave Hello) relative to the 3rd-lowest foot
      const sortedByZ = [...feet].sort((u, v) => u.z - v.z);
      const refZ = sortedByZ[2].z;
      const pass1Feet = feet.filter(f => f.z <= refZ + 22.0);
      const plane1 = this.fitSupportPlane(pass1Feet.length >= 3 ? pass1Feet : sortedByZ.slice(0, 3));

      // Pass 2: Compute signed height above Pass 1 plane & select the supporting polygon (lowest 3..6 feet)
      const withRes = feet.map(f => ({
        ...f,
        r: f.z - (plane1.z0 + plane1.a * f.x + plane1.b * f.y)
      })).sort((u, v) => u.r - v.r);

      const refR = withRes[2].r;
      const supportFeet = withRes.filter(f => f.r <= refR + 7.5);
      const plane2 = this.fitSupportPlane(supportFeet.length >= 3 ? supportFeet : withRes.slice(0, 3));

      // Align support plane normal (-a, 1, -b) in Three.js space with world up (0, 1, 0)
      const normLen = Math.sqrt(plane2.a * plane2.a + 1.0 + plane2.b * plane2.b);
      this.scratchPlaneNormal.set(-plane2.a / normLen, 1.0 / normLen, -plane2.b / normLen);
      this.scratchTargetQuat.setFromUnitVectors(this.scratchPlaneNormal, this.WORLD_UP);
      const targetWorldZ = -80.0 - (plane2.z0 / normLen);

      // Smooth 50 Hz exponential filter to avoid any support-polygon switching pop
      this.chassisWorldQuat.slerp(this.scratchTargetQuat, 0.55);
      this.chassisWorldZ += (targetWorldZ - this.chassisWorldZ) * 0.55;
    }

    if (this.robotRootGroup) {
      this.robotRootGroup.position.set(0, this.chassisWorldZ, 0);
      this.robotRootGroup.quaternion.copy(this.chassisWorldQuat);
    }

    const transformPt = (p: { x: number; y: number; z: number }) => {
      this.scratchVec.set(p.x, p.z, p.y).applyQuaternion(this.chassisWorldQuat);
      return { x: this.scratchVec.x, y: this.scratchVec.z, z: this.scratchVec.y + this.chassisWorldZ };
    };

    const legsWorld: Record<string, any> = {};
    for (const legName in legsBody) {
      const b = legsBody[legName];
      legsWorld[legName] = {
        p0: transformPt(b.p0),
        p1: transformPt(b.p1),
        p2: transformPt(b.p2),
        p3: transformPt(b.p3)
      };
    }

    // Horizontal Stance-Foot Propulsion: scroll & rotate ground grid by planted feet displacement
    let sumDx = 0.0, sumDy = 0.0, sumDAng = 0.0, groundedCount = 0;
    for (const legName in legsWorld) {
      const curr = legsWorld[legName].p3;
      const prev = this.prevWorldFeet[legName];
      if (prev && curr.z <= -76.5 && prev.z <= -76.5) {
        const dfx = curr.x - prev.x;
        const dfy = curr.y - prev.y;
        if (Math.hypot(dfx, dfy) < 25.0) {
          sumDx += dfx;
          sumDy += dfy;
          let dAng = Math.atan2(curr.y, curr.x) - Math.atan2(prev.y, prev.x);
          if (dAng > Math.PI) dAng -= 2 * Math.PI;
          if (dAng < -Math.PI) dAng += 2 * Math.PI;
          sumDAng += dAng;
          groundedCount++;
        }
      }
      this.prevWorldFeet[legName] = { x: curr.x, y: curr.y, z: curr.z };
    }

    if (groundedCount > 0 && this.groundGridGroup && this.groundGrid) {
      const avgDx = sumDx / groundedCount;
      const avgDy = sumDy / groundedCount;
      const avgDAng = sumDAng / groundedCount;

      this.groundYaw -= avgDAng;
      const cosY = Math.cos(this.groundYaw);
      const sinY = Math.sin(this.groundYaw);
      const localDx = avgDx * cosY - avgDy * sinY;
      const localDz = avgDx * sinY + avgDy * cosY;
      const CELL = 20.0;
      this.groundLocalX = (((this.groundLocalX + localDx) % CELL) + CELL) % CELL;
      this.groundLocalZ = (((this.groundLocalZ + localDz) % CELL) + CELL) % CELL;

      this.groundGridGroup.rotation.y = this.groundYaw;
      this.groundGrid.position.set(this.groundLocalX, 0, this.groundLocalZ);
    }

    return legsWorld;
  }

  public update3DLegs(legsBody: any, legsWorld: any = legsBody) {
    if (!this.scene) return;
    const toVec3 = (p: any) => new THREE.Vector3(p.x, p.z, p.y);

    for (const legName in legsBody) {
      const m = this.robot3DMeshes.legs[legName];
      if (!m) continue;

      const pts = legsBody[legName];
      const v0 = toVec3(pts.p0);
      const v1 = toVec3(pts.p1);
      const v2 = toVec3(pts.p2);
      const v3 = toVec3(pts.p3);
      const wPts = legsWorld[legName] || pts;
      const v3World = toVec3(wPts.p3);

      const legDef = this.robotLayout.legs ? this.robotLayout.legs[legName] : null;
      const baseAngle = (legDef && legDef.base_angle !== undefined) ? legDef.base_angle : 0;
      const coxaServoName = legDef && legDef.coxa ? legDef.coxa.name : `${legName}_coxa`;
      const coxaAngle = (this.jointAngles[coxaServoName] || 0) * Math.PI / 180;
      const totalAngle = baseAngle + coxaAngle;

      const normal = new THREE.Vector3(-Math.sin(totalAngle), 0, Math.cos(totalAngle)).normalize();

      const isRightLeg = legName.startsWith('right_');

      // 1. Coxa Segment
      const dir0 = new THREE.Vector3().subVectors(v1, v0);
      if (dir0.length() > 0.001) {
        const axisX0 = dir0.clone().normalize();
        const axisY0 = new THREE.Vector3(0, 1, 0);
        const axisZ0 = new THREE.Vector3().crossVectors(axisX0, axisY0).normalize();
        const mat0 = new THREE.Matrix4().makeBasis(axisX0, axisY0, axisZ0);
        m.coxaGroup.position.copy(v0);
        m.coxaGroup.quaternion.setFromRotationMatrix(mat0);
        const zScale0 = m.coxaGroup.userData?.isStlV2 ? 1 : (isRightLeg ? -1 : 1);
        m.coxaGroup.scale.set(1, 1, zScale0);
      }

      // 2. Femur Segment
      const dir1 = new THREE.Vector3().subVectors(v2, v1);
      if (dir1.length() > 0.001) {
        const axisX1 = dir1.clone().normalize();
        const axisY1 = new THREE.Vector3().crossVectors(normal, axisX1).normalize();
        const axisZ1 = new THREE.Vector3().crossVectors(axisX1, axisY1).normalize();
        const mat1 = new THREE.Matrix4().makeBasis(axisX1, axisY1, axisZ1);
        m.femurGroup.position.copy(v1);
        m.femurGroup.quaternion.setFromRotationMatrix(mat1);
        const zScale1 = m.femurGroup.userData?.isStlV2 ? 1 : (isRightLeg ? -1 : 1);
        m.femurGroup.scale.set(1, 1, zScale1);
      }

      // 3. Tibia Segment
      const dir2 = new THREE.Vector3().subVectors(v3, v2);
      if (dir2.length() > 0.001) {
        const axisY2 = dir2.clone().negate().normalize();
        const axisX2 = new THREE.Vector3().crossVectors(axisY2, normal).normalize();
        const axisZ2 = new THREE.Vector3().crossVectors(axisX2, axisY2).normalize();
        const mat2 = new THREE.Matrix4().makeBasis(axisX2, axisY2, axisZ2);
        m.tibiaGroup.position.copy(v2);
        m.tibiaGroup.quaternion.setFromRotationMatrix(mat2);
        const zScale2 = m.tibiaGroup.userData?.isStlV2 ? 1 : (isRightLeg ? -1 : 1);
        m.tibiaGroup.scale.set(1, 1, zScale2);
      }

      if (legName === this.selectedLegKey) {
        this.lastSelectedLegKinematics = { v0, v1, v2, v3, normal, totalAngle, baseAngle, legDef };
        this.updateAxisGuideLines(v0, v1, v2, normal);
        this.updateMotionRangeArcs();
      }

      // 4. Update Ground Contact Ring & 3D Foot Trajectory Trail (in world coordinates)
      if (this.showFootTrails) {
        const contactRing = this.robot3DMeshes.contactRings[legName];
        if (contactRing) {
          // Ground plane is at y = -80 in Three.js world coordinates
          const isGrounded = v3World.y <= -75.0;
          contactRing.visible = isGrounded;
          contactRing.position.set(v3World.x, -79.6, v3World.z);
          const isSel = legName === this.selectedLegKey;
          contactRing.material.color.setHex(isSel ? 0x38bdf8 : 0x2ecc71);
          contactRing.material.opacity = isSel ? 0.90 : 0.60;
        }

        const trailLine = this.robot3DMeshes.trailLines[legName];
        if (trailLine) {
          const hist = this.footTrailHistory[legName] || (this.footTrailHistory[legName] = []);
          const lastPt = hist[hist.length - 1];
          if (!lastPt || lastPt.distanceToSquared(v3World) > 0.6) {
            hist.push(v3World.clone());
            if (hist.length > this.MAX_TRAIL_POINTS) {
              hist.shift();
            }
            trailLine.geometry.setFromPoints(hist);
          }
          const isSel = legName === this.selectedLegKey;
          trailLine.material.color.setHex(isSel ? 0x38bdf8 : 0x4b5563);
          trailLine.material.opacity = isSel ? 0.85 : 0.35;
        }
      }
    }
  }

  public drawRobot() {
    if (!this.robotLayout.legs) return;

    const legsBody: any = {};
    for (const legName in this.robotLayout.legs) {
      legsBody[legName] = this.computeLeg3D(this.robotLayout.legs[legName], this.jointAngles);
    }

    const legsWorld = this.computeWorldKinematics(legsBody);

    this.update3DLegs(legsBody, legsWorld);
    this.update3DLegHighlights();

    this.syncCanvasDimensions();
    this.drawTopView(legsWorld);
    this.drawFrontView(legsWorld);
    this.drawSideView(legsWorld);
  }

  // --- 2D ORTHOGONAL PROJECTION VIEWS ---

  public drawTopView(legs3D: any) {
    const canvas = this.containers.topCanvas;
    const ctx = this.topCtx;
    const width = canvas.width;
    const height = canvas.height;
    if (width === 0 || height === 0) return;
    ctx.clearRect(0, 0, width, height);

    // Orientation indicator
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.fillText('TOP', 12, 16);

    const centerX = width / 2;
    const centerY = height / 2;
    const scale = Math.min(width / 680, height / 580);

    // 1. Draw outer biomimetic chassis hull (125-point FreeCAD analytical profile)
    const hullPts = this.getChassisHullContour();
    ctx.beginPath();
    for (let i = 0; i < hullPts.length; i++) {
      const x = centerX + hullPts[i].x * scale;
      const y = centerY + hullPts[i].y * scale;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = '#222432';
    ctx.fill();
    ctx.strokeStyle = '#3e425a';
    ctx.lineWidth = 2.0;
    ctx.stroke();

    // 2. v2 Monocoque Chassis Core & Service Cover ('>>>' chevron louvers)
    const coreW = CHASSIS_SPECS.coreWidth * scale;
    const coreL = CHASSIS_SPECS.coreLength * scale;
    ctx.beginPath();
    if ((ctx as any).roundRect) {
      (ctx as any).roundRect(centerX - coreW / 2, centerY - coreL / 2, coreW, coreL, 8 * scale);
    } else {
      ctx.rect(centerX - coreW / 2, centerY - coreL / 2, coreW, coreL);
    }
    ctx.fillStyle = '#262938';
    ctx.fill();
    ctx.strokeStyle = '#3a3f58';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    const srvW = CHASSIS_SPECS.serviceCoverWidth * scale;
    const srvL = CHASSIS_SPECS.serviceCoverLength * scale;
    ctx.beginPath();
    if ((ctx as any).roundRect) {
      (ctx as any).roundRect(centerX - srvW / 2, centerY - srvL / 2, srvW, srvL, 5 * scale);
    } else {
      ctx.rect(centerX - srvW / 2, centerY - srvL / 2, srvW, srvL);
    }
    ctx.fillStyle = '#1b1d2a';
    ctx.fill();
    ctx.strokeStyle = '#32364c';
    ctx.lineWidth = 1.1;
    ctx.stroke();

    // Service Cover '>>>' Chevron Louvers pointing forward (-Y)
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.1;
    for (const ly of [-16, 0, 16]) {
      const cy = centerY + ly * scale;
      ctx.beginPath();
      ctx.moveTo(centerX - 11 * scale, cy + 5 * scale);
      ctx.lineTo(centerX, cy - 4 * scale);
      ctx.lineTo(centerX + 11 * scale, cy + 5 * scale);
      ctx.stroke();
    }

    // 4. 6x Coxa bearing mounting holes (Ø 8 mm)
    const coxaHoleRadiusPx = 4.0 * scale;
    for (const ch of CHASSIS_COXA_HOLES) {
      const cx = centerX + ch.x * scale;
      const cy = centerY + ch.y * scale;
      ctx.beginPath();
      ctx.arc(cx, cy, Math.max(coxaHoleRadiusPx, 2.0), 0, 2 * Math.PI);
      ctx.fillStyle = '#1a1b24';
      ctx.fill();
      ctx.strokeStyle = '#4a5568';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    // 5. Longitudinal center guideline
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.moveTo(centerX, centerY - 100 * scale);
    ctx.lineTo(centerX, centerY + 100 * scale);
    ctx.strokeStyle = '#2d3044';
    ctx.stroke();
    ctx.setLineDash([]);

    // 6. Front direction indicator triangle on top plate pointing to nose apex
    ctx.beginPath();
    ctx.moveTo(centerX - 7 * scale, centerY - 95 * scale);
    ctx.lineTo(centerX + 7 * scale, centerY - 95 * scale);
    ctx.lineTo(centerX, centerY - 110 * scale);
    ctx.closePath();
    ctx.fillStyle = '#38bdf8';
    ctx.fill();

    // 4. Draw each leg in top-down view (unselected first, selected leg on top)
    const legNames = Object.keys(legs3D);
    legNames.sort((a, b) => (a === this.selectedLegKey ? 1 : b === this.selectedLegKey ? -1 : 0));

    this.topViewLegPoints = {};
    for (const legName of legNames) {
      const pts = legs3D[legName];
      if (!pts) continue;
      const isSelected = (legName === this.selectedLegKey);
      const c0 = { x: centerX + pts.p0.x * scale, y: centerY + pts.p0.y * scale };
      const c1 = { x: centerX + pts.p1.x * scale, y: centerY + pts.p1.y * scale };
      const c2 = { x: centerX + pts.p2.x * scale, y: centerY + pts.p2.y * scale };
      const c3 = { x: centerX + pts.p3.x * scale, y: centerY + pts.p3.y * scale };
      this.topViewLegPoints[legName] = { c0, c1, c2, c3 };

      const isCoxaActive = isSelected && (this.currentHoveredJoint === 'coxa');
      const isFemurActive = isSelected && (this.currentHoveredJoint === 'femur');
      const isTibiaActive = isSelected && (this.currentHoveredJoint === 'tibia');

      // Coxa segment
      ctx.beginPath();
      ctx.moveTo(c0.x, c0.y);
      ctx.lineTo(c1.x, c1.y);
      ctx.strokeStyle = isSelected ? (isCoxaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
      ctx.lineWidth = isSelected ? (isCoxaActive ? 4.5 : 3.5) : 2.0;
      ctx.stroke();

      // Femur segment
      ctx.beginPath();
      ctx.moveTo(c1.x, c1.y);
      ctx.lineTo(c2.x, c2.y);
      ctx.strokeStyle = isSelected ? (isFemurActive ? '#38bdf8' : '#2980b9') : '#383a4c';
      ctx.lineWidth = isSelected ? (isFemurActive ? 4.5 : 3.5) : 2.0;
      ctx.stroke();

      // Tibia segment
      ctx.beginPath();
      ctx.moveTo(c2.x, c2.y);
      ctx.lineTo(c3.x, c3.y);
      ctx.strokeStyle = isSelected ? (isTibiaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
      ctx.lineWidth = isSelected ? (isTibiaActive ? 4 : 3) : 1.8;
      ctx.stroke();

      // Chassis mount axis point (c0) - active leg gets Minimap Blue glow #38bdf8
      ctx.fillStyle = isSelected ? '#38bdf8' : '#d0d4de';
      ctx.beginPath();
      ctx.arc(c0.x, c0.y, isSelected ? 4.5 : 3.5, 0, 2 * Math.PI);
      ctx.fill();
      if (isSelected) {
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Joint points
      ctx.fillStyle = isSelected ? '#1b3b5c' : '#282936';
      ctx.beginPath(); ctx.arc(c1.x, c1.y, 3, 0, 2 * Math.PI); ctx.fill();
      ctx.beginPath(); ctx.arc(c2.x, c2.y, 3, 0, 2 * Math.PI); ctx.fill();
      // Foot tip circle completely removed per user request
    }
  }

  public drawFrontView(legs3D: any) {
    const canvas = this.containers.frontCanvas;
    const ctx = this.frontCtx;
    const width = canvas.width;
    const height = canvas.height;
    if (width === 0 || height === 0) return;
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const scale = Math.min(width / 620, height / 290);
    const bodyCanvasY = height * 0.36;
    const groundCanvasY = bodyCanvasY + 80 * scale;

    // 1. Ground Plane (Line with Hatching)
    ctx.strokeStyle = '#3e3e52';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(15, groundCanvasY);
    ctx.lineTo(width - 15, groundCanvasY);
    ctx.stroke();

    ctx.strokeStyle = '#2d2d3d';
    ctx.lineWidth = 1;
    for (let x = 20; x < width - 20; x += 16) {
      ctx.beginPath();
      ctx.moveTo(x, groundCanvasY);
      ctx.lineTo(x - 8, groundCanvasY + 8);
      ctx.stroke();
    }

    // Direction & Level indicators
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.fillText('LEFT', 12, 16);
    ctx.fillText('RIGHT', width - 46, 16);
    ctx.fillText('Ground (-80mm)', 12, groundCanvasY + 14);

    // 2. Depth ordering for Front View
    this.frontViewLegPoints = {};
    for (const legName of ['left_rear', 'right_rear']) {
      if (legs3D[legName]) {
        const isSelected = (legName === this.selectedLegKey);
        this.drawLegFront(ctx, legs3D[legName], centerX, bodyCanvasY, scale, isSelected ? 0.95 : 0.38, isSelected, legName);
      }
    }

    for (const legName of ['left_middle', 'right_middle']) {
      if (legs3D[legName]) {
        const isSelected = (legName === this.selectedLegKey);
        this.drawLegFront(ctx, legs3D[legName], centerX, bodyCanvasY, scale, isSelected ? 0.95 : 0.68, isSelected, legName);
      }
    }

    // 3. Draw v2 Robot Body Chassis (Belly Pan + Dual 2.0 mm Carbon Plates + Monocoque Core + Draped Canopy)
    const halfWidthPx = 88.4 * scale;
    const plateThickPx = Math.max(CHASSIS_SPECS.plateThickness * scale, 2.0);
    const topPlateCanvasY = -CHASSIS_SPECS.topPlateCenterY * scale;
    const botPlateCanvasY = -CHASSIS_SPECS.bottomPlateCenterY * scale;
    const coreH = botPlateCanvasY - topPlateCanvasY;
    const coreHalfW = (CHASSIS_SPECS.coreWidth / 2) * scale;
    const bellyHalfW = (CHASSIS_SPECS.bellyPanWidth / 2) * scale;
    const bellyH = CHASSIS_SPECS.bellyPanDepth * scale;
    const canopyH = CHASSIS_SPECS.canopyHeight * scale;

    const rightVec = new THREE.Vector3(1, 0, 0).applyQuaternion(this.chassisWorldQuat);
    const rollAngleCanvas = Math.atan2(-rightVec.y, rightVec.x);

    ctx.save();
    ctx.translate(centerX, bodyCanvasY - this.chassisWorldZ * scale);
    ctx.rotate(rollAngleCanvas);

    // v2 Monocoque Central Core between carbon plates
    ctx.fillStyle = '#2a2d3d';
    ctx.strokeStyle = '#3e425a';
    ctx.lineWidth = 1.2;
    ctx.fillRect(-coreHalfW, topPlateCanvasY, coreHalfW * 2, coreH);
    ctx.strokeRect(-coreHalfW, topPlateCanvasY, coreHalfW * 2, coreH);

    // v2 Belly Pan beneath bottom plate
    ctx.fillStyle = '#1c1e2a';
    ctx.strokeStyle = '#34384c';
    ctx.fillRect(-bellyHalfW, botPlateCanvasY + plateThickPx / 2, bellyHalfW * 2, bellyH);
    ctx.strokeRect(-bellyHalfW, botPlateCanvasY + plateThickPx / 2, bellyHalfW * 2, bellyH);

    // v2 Draped Translucent Canopy dome above top plate
    ctx.fillStyle = 'rgba(186, 224, 250, 0.22)';
    ctx.strokeStyle = 'rgba(125, 211, 252, 0.55)';
    ctx.beginPath();
    ctx.moveTo(-halfWidthPx * 0.86, topPlateCanvasY - plateThickPx / 2);
    ctx.quadraticCurveTo(-halfWidthPx * 0.65, topPlateCanvasY - canopyH, 0, topPlateCanvasY - canopyH);
    ctx.quadraticCurveTo(halfWidthPx * 0.65, topPlateCanvasY - canopyH, halfWidthPx * 0.86, topPlateCanvasY - plateThickPx / 2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Top & Bottom Carbon Plates
    ctx.fillStyle = '#1c1d26';
    ctx.strokeStyle = '#474c66';
    ctx.lineWidth = 1.8;
    ctx.fillRect(-halfWidthPx, topPlateCanvasY - plateThickPx / 2, halfWidthPx * 2, plateThickPx);
    ctx.strokeRect(-halfWidthPx, topPlateCanvasY - plateThickPx / 2, halfWidthPx * 2, plateThickPx);
    ctx.fillRect(-halfWidthPx, botPlateCanvasY - plateThickPx / 2, halfWidthPx * 2, plateThickPx);
    ctx.strokeRect(-halfWidthPx, botPlateCanvasY - plateThickPx / 2, halfWidthPx * 2, plateThickPx);

    ctx.restore();

    // 4. Front legs (closest to viewer)
    for (const legName of ['left_front', 'right_front']) {
      if (legs3D[legName]) {
        const isSelected = (legName === this.selectedLegKey);
        this.drawLegFront(ctx, legs3D[legName], centerX, bodyCanvasY, scale, 1.0, isSelected, legName);
      }
    }

    // 5. If selected leg is in the background, redraw on top
    if (this.selectedLegKey && !this.selectedLegKey.endsWith('_front') && legs3D[this.selectedLegKey]) {
      this.drawLegFront(ctx, legs3D[this.selectedLegKey], centerX, bodyCanvasY, scale, 1.0, true, this.selectedLegKey);
    }
  }

  private drawLegFront(ctx: CanvasRenderingContext2D, pts: any, centerX: number, bodyCanvasY: number, scale: number, opacity: number, isSelected: boolean, legName: string) {
    ctx.save();
    ctx.globalAlpha = opacity;

    const toCanvas = (p: any) => ({
      x: centerX + p.x * scale,
      y: bodyCanvasY - p.z * scale
    });

    const c0 = toCanvas(pts.p0);
    const c1 = toCanvas(pts.p1);
    const c2 = toCanvas(pts.p2);
    const c3 = toCanvas(pts.p3);

    if (legName) {
      this.frontViewLegPoints[legName] = { c0, c1, c2, c3 };
    }

    const isCoxaActive = isSelected && (this.currentHoveredJoint === 'coxa');
    const isFemurActive = isSelected && (this.currentHoveredJoint === 'femur');
    const isTibiaActive = isSelected && (this.currentHoveredJoint === 'tibia');

    // Coxa segment
    ctx.beginPath();
    ctx.moveTo(c0.x, c0.y);
    ctx.lineTo(c1.x, c1.y);
    ctx.strokeStyle = isSelected ? (isCoxaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isCoxaActive ? 4.5 : 3.5) : 2.0;
    ctx.stroke();

    // Femur segment
    ctx.beginPath();
    ctx.moveTo(c1.x, c1.y);
    ctx.lineTo(c2.x, c2.y);
    ctx.strokeStyle = isSelected ? (isFemurActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isFemurActive ? 4.5 : 3.5) : 2.0;
    ctx.stroke();

    // Tibia segment (straight line)
    ctx.beginPath();
    ctx.moveTo(c2.x, c2.y);
    ctx.lineTo(c3.x, c3.y);
    ctx.strokeStyle = isSelected ? (isTibiaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isTibiaActive ? 4 : 3) : 1.8;
    ctx.stroke();

    // Chassis attachment axis dot (c0)
    ctx.fillStyle = isSelected ? '#38bdf8' : '#d0d4de';
    ctx.beginPath();
    ctx.arc(c0.x, c0.y, isSelected ? 4 : 3.5, 0, 2 * Math.PI);
    ctx.fill();
    if (isSelected) {
      ctx.strokeStyle = '#0284c7';
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }

    // Joint dots
    ctx.fillStyle = isSelected ? '#1b3b5c' : '#282936';
    ctx.beginPath(); ctx.arc(c1.x, c1.y, 3, 0, 2 * Math.PI); ctx.fill();
    ctx.beginPath(); ctx.arc(c2.x, c2.y, 3.5, 0, 2 * Math.PI); ctx.fill();

    ctx.restore();
  }

  public drawSideView(legs3D: any) {
    const canvas = this.containers.sideCanvas;
    const ctx = this.sideCtx;
    const width = canvas.width;
    const height = canvas.height;
    if (width === 0 || height === 0) return;
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const scale = Math.min(width / 580, height / 290);
    const bodyCanvasY = height * 0.36;
    const groundCanvasY = bodyCanvasY + 80 * scale;

    // 1. Ground Plane (Line with Hatching)
    ctx.strokeStyle = '#3e3e52';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(15, groundCanvasY);
    ctx.lineTo(width - 15, groundCanvasY);
    ctx.stroke();

    ctx.strokeStyle = '#2d2d3d';
    ctx.lineWidth = 1;
    for (let x = 20; x < width - 20; x += 16) {
      ctx.beginPath();
      ctx.moveTo(x, groundCanvasY);
      ctx.lineTo(x - 8, groundCanvasY + 8);
      ctx.stroke();
    }

    // Direction & Level indicators
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.fillText('FRONT', 12, 16);
    ctx.fillText('REAR', width - 44, 16);
    ctx.fillText('Ground (-80mm)', 12, groundCanvasY + 14);

    // 2. Draw Left (Far/Background) Legs with dimmed opacity (0.40)
    this.sideViewLegPoints = {};
    for (const legName in legs3D) {
      if (legName.startsWith('left_')) {
        const isSelected = (legName === this.selectedLegKey);
        this.drawLegSide(ctx, legs3D[legName], centerX, bodyCanvasY, scale, isSelected ? 0.95 : 0.40, isSelected, legName);
      }
    }

    // 3. Draw v2 Robot Body Chassis (Side Profile: Belly Pan + Dual 2.0 mm Carbon Plates + Monocoque Core + Draped Canopy)
    const bodyLengthPx = 267.0 * scale;
    const plateThickPx = Math.max(CHASSIS_SPECS.plateThickness * scale, 2.0);
    const topPlateCanvasY = -CHASSIS_SPECS.topPlateCenterY * scale;
    const botPlateCanvasY = -CHASSIS_SPECS.bottomPlateCenterY * scale;
    const coreH = botPlateCanvasY - topPlateCanvasY;
    const coreHalfL = (CHASSIS_SPECS.coreLength / 2) * scale;
    const bellyHalfL = (CHASSIS_SPECS.bellyPanLength / 2) * scale;
    const bellyH = CHASSIS_SPECS.bellyPanDepth * scale;
    const canopyH = CHASSIS_SPECS.canopyHeight * scale;

    const rearVec = new THREE.Vector3(0, 0, 1).applyQuaternion(this.chassisWorldQuat);
    const pitchAngleCanvas = Math.atan2(-rearVec.y, rearVec.z);

    ctx.save();
    ctx.translate(centerX, bodyCanvasY - this.chassisWorldZ * scale);
    ctx.rotate(pitchAngleCanvas);

    // v2 Monocoque Central Core between carbon plates
    ctx.fillStyle = '#2a2d3d';
    ctx.strokeStyle = '#3e425a';
    ctx.lineWidth = 1.2;
    ctx.fillRect(-coreHalfL, topPlateCanvasY, coreHalfL * 2, coreH);
    ctx.strokeRect(-coreHalfL, topPlateCanvasY, coreHalfL * 2, coreH);

    // v2 Belly Pan beneath bottom plate
    ctx.fillStyle = '#1c1e2a';
    ctx.strokeStyle = '#34384c';
    ctx.fillRect(-bellyHalfL, botPlateCanvasY + plateThickPx / 2, bellyHalfL * 2, bellyH);
    ctx.strokeRect(-bellyHalfL, botPlateCanvasY + plateThickPx / 2, bellyHalfL * 2, bellyH);

    // v2 Draped Translucent Canopy dome above top plate
    ctx.fillStyle = 'rgba(186, 224, 250, 0.22)';
    ctx.strokeStyle = 'rgba(125, 211, 252, 0.55)';
    ctx.beginPath();
    ctx.moveTo(-bodyLengthPx * 0.48, topPlateCanvasY - plateThickPx / 2);
    ctx.quadraticCurveTo(-bodyLengthPx * 0.30, topPlateCanvasY - canopyH, 0, topPlateCanvasY - canopyH);
    ctx.quadraticCurveTo(bodyLengthPx * 0.30, topPlateCanvasY - canopyH, bodyLengthPx * 0.48, topPlateCanvasY - plateThickPx / 2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Top & Bottom Carbon Plates
    ctx.fillStyle = '#1c1d26';
    ctx.strokeStyle = '#474c66';
    ctx.lineWidth = 1.8;
    ctx.fillRect(-bodyLengthPx / 2, topPlateCanvasY - plateThickPx / 2, bodyLengthPx, plateThickPx);
    ctx.strokeRect(-bodyLengthPx / 2, topPlateCanvasY - plateThickPx / 2, bodyLengthPx, plateThickPx);
    ctx.fillRect(-bodyLengthPx / 2, botPlateCanvasY - plateThickPx / 2, bodyLengthPx, plateThickPx);
    ctx.strokeRect(-bodyLengthPx / 2, botPlateCanvasY - plateThickPx / 2, bodyLengthPx, plateThickPx);

    // Direction indicator on top plate pointing FRONT (left, towards nose apex)
    ctx.fillStyle = '#38bdf8';
    ctx.beginPath();
    ctx.moveTo(-bodyLengthPx / 2 + 10, topPlateCanvasY - plateThickPx - 3);
    ctx.lineTo(-bodyLengthPx / 2 + 24, topPlateCanvasY - plateThickPx - 9);
    ctx.lineTo(-bodyLengthPx / 2 + 24, topPlateCanvasY - plateThickPx + 3);
    ctx.closePath();
    ctx.fill();

    ctx.restore();

    // 4. Draw Right (Near/Foreground) Legs with full opacity (1.0)
    for (const legName in legs3D) {
      if (legName.startsWith('right_')) {
        const isSelected = (legName === this.selectedLegKey);
        this.drawLegSide(ctx, legs3D[legName], centerX, bodyCanvasY, scale, 1.0, isSelected, legName);
      }
    }

    // 5. If selected leg is in the background (left side), redraw on top
    if (this.selectedLegKey && this.selectedLegKey.startsWith('left_') && legs3D[this.selectedLegKey]) {
      this.drawLegSide(ctx, legs3D[this.selectedLegKey], centerX, bodyCanvasY, scale, 1.0, true, this.selectedLegKey);
    }
  }

  private drawLegSide(ctx: CanvasRenderingContext2D, pts: any, centerX: number, bodyCanvasY: number, scale: number, opacity: number, isSelected: boolean, legName: string) {
    ctx.save();
    ctx.globalAlpha = opacity;

    const toCanvas = (p: any) => ({
      x: centerX + p.y * scale,
      y: bodyCanvasY - p.z * scale
    });

    const c0 = toCanvas(pts.p0);
    const c1 = toCanvas(pts.p1);
    const c2 = toCanvas(pts.p2);
    const c3 = toCanvas(pts.p3);

    if (legName) {
      this.sideViewLegPoints[legName] = { c0, c1, c2, c3 };
    }

    const isCoxaActive = isSelected && (this.currentHoveredJoint === 'coxa');
    const isFemurActive = isSelected && (this.currentHoveredJoint === 'femur');
    const isTibiaActive = isSelected && (this.currentHoveredJoint === 'tibia');

    // Coxa segment
    ctx.beginPath();
    ctx.moveTo(c0.x, c0.y);
    ctx.lineTo(c1.x, c1.y);
    ctx.strokeStyle = isSelected ? (isCoxaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isCoxaActive ? 4.5 : 3.5) : 2.0;
    ctx.stroke();

    // Femur segment
    ctx.beginPath();
    ctx.moveTo(c1.x, c1.y);
    ctx.lineTo(c2.x, c2.y);
    ctx.strokeStyle = isSelected ? (isFemurActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isFemurActive ? 4.5 : 3.5) : 2.0;
    ctx.stroke();

    // Tibia segment (straight line)
    ctx.beginPath();
    ctx.moveTo(c2.x, c2.y);
    ctx.lineTo(c3.x, c3.y);
    ctx.strokeStyle = isSelected ? (isTibiaActive ? '#38bdf8' : '#2980b9') : '#383a4c';
    ctx.lineWidth = isSelected ? (isTibiaActive ? 4 : 3) : 1.8;
    ctx.stroke();

    // Chassis attachment axis dot (c0)
    ctx.fillStyle = isSelected ? '#38bdf8' : '#d0d4de';
    ctx.beginPath();
    ctx.arc(c0.x, c0.y, isSelected ? 4 : 3.5, 0, 2 * Math.PI);
    ctx.fill();
    if (isSelected) {
      ctx.strokeStyle = '#0284c7';
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }

    // Joint dots
    ctx.fillStyle = isSelected ? '#1b3b5c' : '#282936';
    ctx.beginPath(); ctx.arc(c1.x, c1.y, 3, 0, 2 * Math.PI); ctx.fill();
    ctx.beginPath(); ctx.arc(c2.x, c2.y, 3.5, 0, 2 * Math.PI); ctx.fill();

    ctx.restore();
  }

  // --- HIT DETECTION & INTERACTION ---

  private distToSegmentSquared(p: { x: number; y: number }, v: { x: number; y: number }, w: { x: number; y: number }) {
    const l2 = (v.x - w.x) * (v.x - w.x) + (v.y - w.y) * (v.y - w.y);
    if (l2 === 0) return (p.x - v.x) * (p.x - v.x) + (p.y - v.y) * (p.y - v.y);
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    const projX = v.x + t * (w.x - v.x);
    const projY = v.y + t * (w.y - v.y);
    return (p.x - projX) * (p.x - projX) + (p.y - projY) * (p.y - projY);
  }

  private findClickedLeg(canvas: HTMLCanvasElement, e: MouseEvent, legPointsMap: Record<string, any>): string | null {
    if (!canvas || !legPointsMap) return null;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return null;
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const p = {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };

    let closestLeg: string | null = null;
    let minD2 = 28 * 28; // 28px hit tolerance

    for (const legName in legPointsMap) {
      const pts = legPointsMap[legName];
      if (!pts || !pts.c0 || !pts.c1 || !pts.c2 || !pts.c3) continue;
      const d0 = this.distToSegmentSquared(p, pts.c0, pts.c1);
      const d1 = this.distToSegmentSquared(p, pts.c1, pts.c2);
      const d2 = this.distToSegmentSquared(p, pts.c2, pts.c3);
      const dMin = Math.min(d0, d1, d2);
      if (dMin < minD2) {
        minD2 = dMin;
        closestLeg = legName;
      }
    }
    return closestLeg;
  }

  private setupEvents() {
    // 2D Canvases Click & Hover
    [
      { canvas: this.containers.topCanvas, getMap: () => this.topViewLegPoints },
      { canvas: this.containers.frontCanvas, getMap: () => this.frontViewLegPoints },
      { canvas: this.containers.sideCanvas, getMap: () => this.sideViewLegPoints }
    ].forEach(({ canvas, getMap }) => {
      canvas.addEventListener('click', (e) => {
        const leg = this.findClickedLeg(canvas, e, getMap());
        if (leg) {
          this.selectedLegKey = leg;
          this.callbacks.onSelectLeg(leg);
          this.drawRobot();
        }
      });

      canvas.addEventListener('mousemove', (e) => {
        const leg = this.findClickedLeg(canvas, e, getMap());
        canvas.style.cursor = leg ? 'pointer' : 'default';
      });

      canvas.addEventListener('mouseleave', () => {
        canvas.style.cursor = 'default';
      });
    });

    // 3D Canvas Click Raycaster
    const dom = this.renderer.domElement;
    dom.addEventListener('click', (e) => {
      const rect = dom.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);

      const candidates: THREE.Mesh[] = [];
      for (const legName in this.robot3DMeshes.legs) {
        const leg = this.robot3DMeshes.legs[legName];
        if (!leg) continue;
        [leg.coxaGroup, leg.femurGroup, leg.tibiaGroup].forEach(g => {
          if (g) {
            g.traverse((child: any) => {
              if (child.isMesh) {
                child.userData.legName = legName;
                candidates.push(child);
              }
            });
          }
        });
      }

      const intersects = this.raycaster.intersectObjects(candidates, false);
      if (intersects.length > 0) {
        const hitLeg = intersects[0].object.userData.legName;
        if (hitLeg) {
          this.selectedLegKey = hitLeg;
          this.callbacks.onSelectLeg(hitLeg);
          this.drawRobot();
        }
      }
    });

    // 3D Canvas Joint Hover
    dom.addEventListener('pointermove', (e) => {
      const rect = dom.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);

      const activeLeg = this.robot3DMeshes.legs[this.selectedLegKey];
      if (!activeLeg) return;

      const candidates: THREE.Mesh[] = [];
      [activeLeg.coxaGroup, activeLeg.femurGroup, activeLeg.tibiaGroup].forEach(g => {
        if (g) {
          g.traverse((child: any) => {
            if (child.isMesh && child.userData && child.userData.jointType) {
              candidates.push(child);
            }
          });
        }
      });

      const intersects = this.raycaster.intersectObjects(candidates, false);
      if (intersects.length > 0) {
        const jointType = intersects[0].object.userData.jointType;
        if (this.currentHoveredJoint !== jointType) {
          this.currentHoveredJoint = jointType;
          this.callbacks.onHoverJoint(jointType);
          this.update3DLegHighlights(this.selectedLegKey, this.currentHoveredJoint);
          this.updateMotionRangeArcs();
          this.drawRobot();
        }
      } else {
        if (this.currentHoveredJoint !== null) {
          this.currentHoveredJoint = null;
          this.callbacks.onHoverJoint(null);
          this.update3DLegHighlights(this.selectedLegKey, null);
          this.updateMotionRangeArcs();
          this.drawRobot();
        }
      }
    });

    dom.addEventListener('pointerleave', () => {
      if (this.currentHoveredJoint !== null) {
        this.currentHoveredJoint = null;
        this.callbacks.onHoverJoint(null);
        this.update3DLegHighlights(this.selectedLegKey, null);
        this.updateMotionRangeArcs();
        this.drawRobot();
      }
    });

    // Resize Observer
    if (window.ResizeObserver) {
      this.resizeObserver = new ResizeObserver(() => {
        this.resize();
      });
      this.resizeObserver.observe(this.containers.threeContainer);
      this.resizeObserver.observe(this.containers.topCanvas);
    }
  }

  public setJointAngles(angles: Record<string, number>) {
    Object.assign(this.jointAngles, angles);
    this.drawRobot();
  }

  public setSelectedLegKey(legKey: string) {
    this.selectedLegKey = legKey;
    this.drawRobot();
  }

  public setCurrentHoveredJoint(joint: 'coxa' | 'femur' | 'tibia' | null) {
    this.currentHoveredJoint = joint;
    this.update3DLegHighlights();
    this.updateMotionRangeArcs();
    this.drawRobot();
  }

  public setCalibrationData(data: Record<string, any>) {
    this.calibrationData = data;
    this.updateMotionRangeArcs();
  }

  private saveCameraState() {
    if (!this.camera || !this.controls) return;
    try {
      const state = {
        pos: [
          Number(this.camera.position.x.toFixed(2)),
          Number(this.camera.position.y.toFixed(2)),
          Number(this.camera.position.z.toFixed(2))
        ],
        target: [
          Number(this.controls.target.x.toFixed(2)),
          Number(this.controls.target.y.toFixed(2)),
          Number(this.controls.target.z.toFixed(2))
        ]
      };
      localStorage.setItem(this.CAMERA_STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Ignore storage quota or privacy mode errors
    }
  }

  private restoreCameraState() {
    if (!this.camera || !this.controls) return;
    try {
      const raw = localStorage.getItem(this.CAMERA_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (
        Array.isArray(parsed?.pos) &&
        parsed.pos.length === 3 &&
        parsed.pos.every((n: unknown) => typeof n === 'number' && Number.isFinite(n)) &&
        Array.isArray(parsed?.target) &&
        parsed.target.length === 3 &&
        parsed.target.every((n: unknown) => typeof n === 'number' && Number.isFinite(n))
      ) {
        this.camera.position.set(parsed.pos[0], parsed.pos[1], parsed.pos[2]);
        this.controls.target.set(parsed.target[0], parsed.target[1], parsed.target[2]);
        this.controls.update();
      }
    } catch {
      // Ignore malformed state
    }
  }

  public resetCamera() {
    if (this.camera && this.controls) {
      if (this.cameraSaveTimer) {
        clearTimeout(this.cameraSaveTimer);
        this.cameraSaveTimer = null;
      }
      try {
        localStorage.removeItem(this.CAMERA_STORAGE_KEY);
      } catch {
        // Ignore storage errors
      }
      this.camera.position.set(380, 280, 380);
      this.controls.target.set(0, -25, 0);
      this.controls.update();
    }
  }

  public resize() {
    const el = this.containers.threeContainer;
    const width = el.clientWidth || 820;
    const height = el.clientHeight || 520;
    if (this.renderer && this.camera) {
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }
    this.syncCanvasDimensions();
    this.drawRobot();
  }

  public destroy() {
    if (this.cameraSaveTimer) {
      clearTimeout(this.cameraSaveTimer);
      this.cameraSaveTimer = null;
    }
    if (this.animFrameId !== null) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }

    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }

    if (this.controls) this.controls.dispose();
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer.forceContextLoss();
      if (this.renderer.domElement.parentElement) {
        this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
      }
    }
  }
}

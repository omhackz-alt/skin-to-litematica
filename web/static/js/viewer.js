/**
 * Three.js 3D Voxel Viewer
 * Renders block sculptures in WebGL
 */

class VoxelViewer {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.blockMesh = null;

        this.init();
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);

        // Camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(30, 30, 30);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        // Orbit Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 50, 50);
        this.scene.add(directionalLight);

        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight2.position.set(-50, 50, -50);
        this.scene.add(directionalLight2);

        // Handle resize
        window.addEventListener('resize', () => this.onResize());

        // Start animation loop
        this.animate();
    }

    loadBlocks(blocks, dimensions) {
        // Remove existing mesh
        if (this.blockMesh) {
            this.scene.remove(this.blockMesh);
            this.blockMesh.geometry.dispose();
            this.blockMesh.material.forEach(m => m.dispose());
        }

        // Create merged geometry for performance
        const geometry = new THREE.BoxGeometry(1, 1, 1);
        const materials = {};
        const meshes = [];

        blocks.forEach(block => {
            const color = block.color;

            if (!materials[color]) {
                materials[color] = new THREE.MeshLambertMaterial({
                    color: new THREE.Color(color)
                });
            }

            const cube = new THREE.Mesh(geometry, materials[color]);
            cube.position.set(
                block.x - dimensions[0] / 2,
                block.y,
                block.z - dimensions[2] / 2
            );
            meshes.push(cube);
        });

        // Create group
        this.blockMesh = new THREE.Group();
        meshes.forEach(mesh => this.blockMesh.add(mesh));
        this.scene.add(this.blockMesh);

        // Center camera on model
        const maxDim = Math.max(...dimensions);
        this.camera.position.set(maxDim * 1.5, maxDim * 1.2, maxDim * 1.5);
        this.controls.target.set(0, dimensions[1] / 2, 0);
        this.controls.update();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    onResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    dispose() {
        if (this.blockMesh) {
            this.scene.remove(this.blockMesh);
        }
        this.renderer.dispose();
        this.container.innerHTML = '';
    }
}

// Mini preview renderer for result cards
class MiniPreview {
    constructor(container, blocks, dimensions) {
        this.container = container;

        // Scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf1f3f4);

        // Camera
        const width = container.clientWidth || 200;
        const height = container.clientHeight || 150;
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);

        const maxDim = Math.max(...dimensions);
        camera.position.set(maxDim * 1.2, maxDim * 0.8, maxDim * 1.2);
        camera.lookAt(0, dimensions[1] / 2, 0);

        // Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Lighting
        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
        dirLight.position.set(30, 30, 30);
        scene.add(dirLight);

        // Create blocks (simplified for performance)
        const geometry = new THREE.BoxGeometry(1, 1, 1);
        const group = new THREE.Group();

        // Sample blocks if too many
        const maxBlocks = 500;
        const step = blocks.length > maxBlocks ? Math.ceil(blocks.length / maxBlocks) : 1;

        for (let i = 0; i < blocks.length; i += step) {
            const block = blocks[i];
            const material = new THREE.MeshLambertMaterial({
                color: new THREE.Color(block.color)
            });
            const cube = new THREE.Mesh(geometry, material);
            cube.position.set(
                block.x - dimensions[0] / 2,
                block.y,
                block.z - dimensions[2] / 2
            );
            group.add(cube);
        }

        scene.add(group);

        // Rotate animation
        let angle = 0;
        const animate = () => {
            requestAnimationFrame(animate);
            angle += 0.01;
            group.rotation.y = angle;
            renderer.render(scene, camera);
        };
        animate();
    }
}

window.VoxelViewer = VoxelViewer;
window.MiniPreview = MiniPreview;

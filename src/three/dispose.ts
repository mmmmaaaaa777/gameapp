import * as THREE from "three";

function disposeMaterial(material: THREE.Material): void {
  const materialWithTextures = material as THREE.Material & {
    map?: THREE.Texture | null;
    alphaMap?: THREE.Texture | null;
    emissiveMap?: THREE.Texture | null;
  };

  materialWithTextures.map?.dispose();
  materialWithTextures.alphaMap?.dispose();
  materialWithTextures.emissiveMap?.dispose();
  material.dispose();
}

export function disposeObject3D(object: THREE.Object3D): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh;

    if (mesh.geometry) {
      mesh.geometry.dispose();
    }

    const material = mesh.material;

    if (Array.isArray(material)) {
      material.forEach(disposeMaterial);
    } else if (material) {
      disposeMaterial(material);
    }
  });
}

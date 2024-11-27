#!/usr/bin/env python3
import sys
import time
import numpy as np


def xyz_reader(
    filename,
    box_info=False,
    indexed=False,
    start=1,
    stop=-1,
    step=1,
    max_frames=None,
    stream=False,
    interval=2.0,
    sleep=time.sleep,
):
    if stop > 0 and start > stop:
        return
    pf = open(filename, "r")
    inside_frame = False
    nat_read = False
    iframe = 0
    stride = step
    nframes = 0
    if start > 1:
        print(f"skipping {start-1} frames")
    if not box_info:
        box = None
    while True:
        line = pf.readline()

        if not line:
            if stream:
                sleep(interval)
                continue
            elif inside_frame or nat_read:
                raise Exception("Error: premature end of file!")
            else:
                break

        line = line.strip()
        if line.startswith("#"):
            continue

        if not inside_frame:
            if not nat_read:
                nat = int(line.split()[0])
                nat_read = True
                iat = 0
                inside_frame = not box_info
                xyz = np.zeros((nat, 3))
                species = []
                continue

            box = np.array(line.split(), dtype="float")
            inside_frame = True
            continue

        ls = line.split()
        iat, s = (int(ls[0]), 1) if indexed else (iat + 1, 0)
        species.append(ls[s])
        xyz[iat - 1, :] = np.array([ls[s + 1], ls[s + 2], ls[s + 3]], dtype="float")
        if iat == nat:
            iframe += 1
            inside_frame = False
            nat_read = False
            if iframe < start:
                continue
            stride += 1
            if stride >= step:
                nframes += 1
                stride = 0
                yield np.array(species, dtype="<U2"), xyz, box
            if (max_frames is not None and nframes >= max_frames) or (
                stop > 0 and iframe >= stop
            ):
                break


def apply_pbc(xyz, pairs, cell, rmax, minimum_image):
    cellinv = np.linalg.inv(cell)
    if minimum_image:
        vec = xyz[pairs[1]] - xyz[pairs[0]]
        # q = cellinv @ vec.T
        shift = -np.round(
            np.dot(vec, cellinv.T)
        )  # np.einsum("ij,sj->si", cellinv, vec)
        vec = vec + np.dot(shift, cell.T)  # np.einsum("ij,sj->si", cell, q)
        # return (cell @ q).T
    else:
        shift = -np.floor(np.dot(xyz, cellinv.T))
        xyz_pbc = xyz + np.dot(shift, cell.T)

        inv_distances = np.sum(cellinv**2, axis=0) ** 0.5
        num_repeats = np.ceil(rmax * inv_distances).astype(np.int32)
        cell_shift_pbc = np.array(
            np.meshgrid(*[np.arange(-n, n + 1) for n in num_repeats])
        ).T.reshape(-1, 3)
        dvec = np.dot(cell_shift_pbc, cell.T)

        vec = (
            (xyz_pbc[pairs[1]] - xyz_pbc[pairs[0]])[:, None, :] + dvec[None, :, :]
        ).reshape(-1, 3)
    return vec


def get_pairs(species, sp1=None, sp2=None):
    # nat=len(species)
    # id1=np.flatnonzero(species==sp1) if sp1 is not None else np.arange(nat)
    # if sp2 != sp1:
    #  id2=np.flatnonzero(species==sp2) if sp2 is not None else np.arange(nat)
    # pairs=np.array([np.repeat(id1, len(id2)),np.tile(id2, len(id1))])
    # if sp1 is None or sp2 is None or sp1==sp2:
    #  pairs=pairs[:,pairs[0]!=pairs[1]]
    # return pairs
    # if sp1 is None and sp2 is not None: sp1=sp2
    # if sp2 is None and sp1 is not None: sp2=sp1
    if sp1 is None:
        if sp2 is None:
            return np.array(np.triu_indices(len(species), 1)), 0.5 * len(species) ** 2
        sp1 = sp2
    id1 = np.flatnonzero(species == sp1)
    num1 = len(id1)
    if sp2 == sp1 or sp2 is None:
        pairsloc = np.triu_indices(len(id1), 1)
        return np.array([id1[pairsloc[0]], id1[pairsloc[1]]]), 0.5 * num1**2
    id2 = np.flatnonzero(species == sp2)
    num2 = len(id2)
    return np.array([np.repeat(id1, len(id2)), np.tile(id2, len(id1))]), num1 * num2


def radial_density(
    species,
    xyz,
    cell=None,
    rmax=10.0,
    dr=0.1,
    sp1=None,
    sp2=None,
    pairs=None,
    timer=False,
    minimum_image=False,
):
    nat = len(species)
    if timer:
        print(sp1, sp2)
        time0 = time.time()
    if pairs is None:
        pairs, n_pairs_norm = get_pairs(species, sp1, sp2)
    n_pairs = pairs.shape[1]
    mult = 1 if sp1 != sp2 else 2
    # print(mult*n_pairs,mult)
    if timer:
        print("pairs:", time.time() - time0)
        time0 = time.time()
    if cell is not None:
        vec = apply_pbc(xyz, pairs, cell, rmax, minimum_image)
    else:
        vec = xyz[pairs[0]] - xyz[pairs[1]]
    dist = np.linalg.norm(vec, axis=-1)
    #if sp1 == "O" and sp2 =="O":
    #  mask = (dist < 2.).nonzero()[0]
    #  for i in mask:
    #    print(pairs[0,i],pairs[1,i],dist[i])

    if timer:
        print("dists:", time.time() - time0)
        time0 = time.time()
    n_bins = int(rmax / dr)
    bins = np.linspace(0, rmax, n_bins + 1)
    r, _ = np.histogram(dist, bins=n_bins, range=(0, rmax))
    if timer:
        print("hist:", time.time() - time0)
    expect = n_pairs_norm * 4.0 / 3.0 * np.pi * ((bins[1:]) ** 3 - bins[:-1] ** 3)
    if cell is not None:
        volume = np.dot(cell[:, 0], np.cross(cell[:, 1], cell[:, 2]))
        expect /= volume
    return r / expect


def radial_from_file(
    xyzfile,
    pairs,
    outfile="gr.dat",
    rmax=10,
    dr=0.02,
    thermalize=0,
    stride=1,
    box_info=False,
    indexed=False,
    watch=False,
    cell=None,
    minimum_image=False,
    **kwargs,
):
    if "tinker" in kwargs and kwargs["tinker"]:
        indexed = True
        box_info = True

    abox=cell[0,0]
    nbins_diff = 50
    bins = np.linspace(0,1.2,nbins_diff+1)
    bin_centers = 0.5*(bins[1:]+bins[:-1])
    hist_full = np.zeros(nbins_diff)

    try:
        # frames = list(read_arc_file(arcfile,max_frames=205))
        # print(len(frames))
        reader = xyz_reader(
            xyzfile,
            box_info=box_info,
            indexed=indexed,
            start=thermalize + 1,
            step=stride,
            stream=watch,
        )
        n_bins = int(rmax / dr)
        centers = (np.arange(n_bins) + 0.5) * dr
        nframe = 0
        if cell is not None:
            # cell=np.array([float(c) for c in cell.split()]).reshape((3,3),order="F")
            cell = np.array(cell).reshape((3, 3), order="F")
            print("cell matrix=")
            print(cell)
        # setup_figures(["g(r)"])
        # plt.pause(1.)
        pairs = [p.strip().replace("-", " ").replace("_", " ") for p in pairs]
        header = " ".join(["r"] + ["-".join(p.split()) for p in pairs])
        box = None
        gr_avg = np.zeros((n_bins, len(pairs)))
        OHmin_sum = 0
        OOmean_sum = 0
        for frame in reader:
            species, xyz, box = frame
            if box is not None:
                cell = np.diag(box[:3])
            nframe += 1
            print(nframe)
            for i, pair in enumerate(pairs):
                sp1, sp2 = pair.split()
                gr = radial_density(
                    species, xyz, cell, rmax, dr, sp1=sp1, sp2=sp2, timer=False, minimum_image=minimum_image
                )
                # gr=radial_density_numba(species,xyz,box,rmax,dr,sp1=sp1,sp2=sp2)
                gr_avg[:, i] += gr
            # cleanup_ax(plt.gca())
            # plt.plot(centers,gr_avg/nframe)
            # plt.pause(1.)
            np.savetxt(
                f'gr_{abox:.2f}.dat', np.column_stack((centers, gr_avg / nframe)), header=header
            )

            # get distance difference
            cellinv = np.linalg.inv(cell)
            H_indices = (species=="H").nonzero()[0]
            O_indices = (species=="O").nonzero()[0]
            vec = xyz[H_indices,None,:]-xyz[None,O_indices,:]
            shift = -np.round(
                np.einsum("ij,asj->asi", cellinv, vec)
            )  
            vec = vec + np.einsum("ij,asj->asi", cell, shift)
            all_distances = np.linalg.norm(vec,axis=-1)
            distances = np.sort(all_distances,axis=1)[:,:2]
            if nframe == 1:
              iObond = np.arange(len(H_indices))*len(O_indices) + np.argmin(all_distances,axis=1)
            OHmin = np.mean(all_distances.flatten()[iObond])
            OHmin_sum += OHmin
              
            xi = distances[:,1]-distances[:,0]
            hist,_ = np.histogram(xi,bins=bins,density=False)
            hist_full = hist_full + hist
            np.savetxt(f'diffOH_{abox:.2f}.dat',np.column_stack((bin_centers,hist_full/nframe/len(H_indices))))

            vec = xyz[O_indices,None,:]-xyz[None,O_indices,:]
            shift = -np.round(
                np.einsum("ij,asj->asi", cellinv, vec)
            )  
            vec = vec + np.einsum("ij,asj->asi", cell, shift)
            all_distances = np.linalg.norm(vec,axis=-1)
            distances = np.sort(all_distances,axis=1)[:,1:9]
            OOmean_sum += np.mean(distances)

            np.savetxt(f'OHmin_OO_{abox:.2f}.dat',np.array((abox,OHmin_sum/nframe,OOmean_sum/nframe, OHmin_sum/OOmean_sum))[None,:])

            


    except KeyboardInterrupt:
        sys.exit(0)


def main(xyzfile: str, thermalize: int = 0, watch: bool = False, minimum_image=False,a=9.):

    # box length
    cell = np.array([a, 0, 0, 0, a, 0, 0, 0, a]).reshape((3, 3), order="F")

    # maximum distance to compute the rdf
    rmax = 9.
    # bin width
    dr = 0.02

    # pairs of atoms to compute the rdf
    pairs = ["O O", "O H", "H H"]

    radial_from_file(
        xyzfile,
        pairs,
        cell=cell,
        rmax=rmax,
        dr=dr,
        indexed=True,
        box_info=False,
        watch=watch,
        thermalize=thermalize,
        minimum_image=minimum_image,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="compute radial distribution function")
    parser.add_argument("arcfile", type=str, help="arc file")
    parser.add_argument("a", type=float, help="box size")
    parser.add_argument(
        "--thermalize", "-t", type=int, default=0, help="number of frames to skip"
    )
    parser.add_argument("--watch", "-w", action="store_true", help="watch file")
    parser.add_argument("--minimage", action="store_true", help="watch file")
    args = parser.parse_args()
    main(args.arcfile, args.thermalize, args.watch, args.minimage,args.a)

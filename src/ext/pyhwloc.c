/*
 * Copyright (c) 2025-2026, NVIDIA CORPORATION.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */
#include "pyhwloc_export.h"
#include <hwloc.h>

PYHWLOC_EXPORT int pyhwloc_get_type_or_below_depth(hwloc_topology_t topology,
                                                   hwloc_obj_type_t type) {
  return hwloc_get_type_or_below_depth(topology, type);
}

PYHWLOC_EXPORT void *pyhwloc_alloc_membind_policy(hwloc_topology_t topology,
                                                  size_t len,
                                                  hwloc_const_cpuset_t set,
                                                  hwloc_membind_policy_t policy,
                                                  int flags) {
  return hwloc_alloc_membind_policy(topology, len, set, policy, flags);
}

// Object levels, depths and types
PYHWLOC_EXPORT int pyhwloc_get_type_or_above_depth(hwloc_topology_t topology,
                                                   hwloc_obj_type_t type) {

  return hwloc_get_type_or_above_depth(topology, type);
}

PYHWLOC_EXPORT int pyhwloc_get_nbobjs_by_type(hwloc_topology_t topology,
                                              hwloc_obj_type_t type) {
  return hwloc_get_nbobjs_by_type(topology, type);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_root_obj(hwloc_topology_t topology) {

  return hwloc_get_root_obj(topology);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_by_type(hwloc_topology_t topology,
                                                   hwloc_obj_type_t type,
                                                   unsigned idx) {

  return hwloc_get_obj_by_type(topology, type, idx);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_by_depth(
    hwloc_topology_t topology, int depth, hwloc_obj_t prev) {

  return hwloc_get_next_obj_by_depth(topology, depth, prev);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_by_type(
    hwloc_topology_t topology, hwloc_obj_type_t type, hwloc_obj_t prev) {
  return hwloc_get_next_obj_by_type(topology, type, prev);
}

// Consulting and Adding Info Attributes
PYHWLOC_EXPORT int pyhwloc_obj_add_info(hwloc_obj_t obj, const char *name,
                                        const char *value) {
  return hwloc_obj_add_info(obj, name, value);
}

#define HWLOC_API_VERSION_MAJOR (HWLOC_API_VERSION >> 16)

#if HWLOC_API_VERSION_MAJOR >= 3
PYHWLOC_EXPORT char const *pyhwloc_get_info_by_name(struct hwloc_infos_s *infos,
                                                    const char *name) {

  return hwloc_get_info_by_name(infos, name);
}
#elif HWLOC_API_VERSION_MAJOR >= 2
PYHWLOC_EXPORT char const *pyhwloc_obj_get_info_by_name(hwloc_obj_t obj,
                                                        const char *name) {
  return hwloc_obj_get_info_by_name(obj, name);
}
#else
/* nothing, should lead to a missing symbol error in Python. */
#endif

// Finding I/O objects
PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_non_io_ancestor_obj(
    hwloc_topology_t topology __hwloc_attribute_unused, hwloc_obj_t ioobj) {
  return hwloc_get_non_io_ancestor_obj(topology, ioobj);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_pcidev(hwloc_topology_t topology,
                                                   hwloc_obj_t prev) {
  return hwloc_get_next_pcidev(topology, prev);
}

PYHWLOC_EXPORT hwloc_obj_t
pyhwloc_get_pcidev_by_busid(hwloc_topology_t topology, unsigned domain,
                            unsigned bus, unsigned dev, unsigned func) {
  return hwloc_get_pcidev_by_busid(topology, domain, bus, dev, func);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_pcidev_by_busidstring(
    hwloc_topology_t topology, const char *busid) {
  return hwloc_get_pcidev_by_busidstring(topology, busid);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_osdev(hwloc_topology_t topology,
                                                  hwloc_obj_t prev) {
  return hwloc_get_next_osdev(topology, prev);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_bridge(hwloc_topology_t topology,
                                                   hwloc_obj_t prev) {
  return hwloc_get_next_bridge(topology, prev);
}

PYHWLOC_EXPORT int pyhwloc_bridge_covers_pcibus(hwloc_obj_t bridge,
                                                unsigned domain, unsigned bus) {

  return hwloc_bridge_covers_pcibus(bridge, domain, bus);
}

// Looking at Cache Objects
PYHWLOC_EXPORT int
pyhwloc_get_cache_type_depth(hwloc_topology_t topology, unsigned cachelevel,
                             hwloc_obj_cache_type_t cachetype) {

  return hwloc_get_cache_type_depth(topology, cachelevel, cachetype);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_cache_covering_cpuset(
    hwloc_topology_t topology, hwloc_const_cpuset_t set) {
  return hwloc_get_cache_covering_cpuset(topology, set);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_shared_cache_covering_obj(
    hwloc_topology_t topology __hwloc_attribute_unused, hwloc_obj_t obj) {
  return hwloc_get_shared_cache_covering_obj(topology, obj);
}

// Finding objects, miscellaneous helpers
PYHWLOC_EXPORT int pyhwloc_bitmap_singlify_per_core(hwloc_topology_t topology,
                                                    hwloc_bitmap_t cpuset,
                                                    unsigned which) {
  return hwloc_bitmap_singlify_per_core(topology, cpuset, which);
}

PYHWLOC_EXPORT hwloc_obj_t
pyhwloc_get_pu_obj_by_os_index(hwloc_topology_t topology, unsigned os_index) {
  return hwloc_get_pu_obj_by_os_index(topology, os_index);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_numanode_obj_by_os_index(
    hwloc_topology_t topology, unsigned os_index) {
  return hwloc_get_numanode_obj_by_os_index(topology, os_index);
}

PYHWLOC_EXPORT unsigned pyhwloc_get_closest_objs(hwloc_topology_t topology,
                                                 hwloc_obj_t src,
                                                 hwloc_obj_t *objs,
                                                 unsigned max) {
  return hwloc_get_closest_objs(topology, src, objs, max);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_below_by_type(
    hwloc_topology_t topology, hwloc_obj_type_t type1, unsigned idx1,
    hwloc_obj_type_t type2, unsigned idx2) {
  return hwloc_get_obj_below_by_type(topology, type1, idx1, type2, idx2);
}

PYHWLOC_EXPORT hwloc_obj_t
pyhwloc_get_obj_below_array_by_type(hwloc_topology_t topology, int nr,
                                    hwloc_obj_type_t *typev, unsigned *idxv) {
  return hwloc_get_obj_below_array_by_type(topology, nr, typev, idxv);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_with_same_locality(
    hwloc_topology_t topology, hwloc_obj_t src, hwloc_obj_type_t type,
    const char *subtype, const char *nameprefix, unsigned long flags) {
  return hwloc_get_obj_with_same_locality(topology, src, type, subtype,
                                          nameprefix, flags);
}

// Converting between CPU sets and node sets
PYHWLOC_EXPORT int pyhwloc_cpuset_to_nodeset(hwloc_topology_t topology,
                                             hwloc_const_cpuset_t cpuset,
                                             hwloc_nodeset_t nodeset) {
  return hwloc_cpuset_to_nodeset(topology, cpuset, nodeset);
}

PYHWLOC_EXPORT int pyhwloc_cpuset_from_nodeset(hwloc_topology_t topology,
                                               hwloc_cpuset_t cpuset,
                                               hwloc_const_nodeset_t nodeset) {
  return hwloc_cpuset_from_nodeset(topology, cpuset, nodeset);
}

// Finding objects covering at least a CPU set
PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_child_covering_cpuset(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset,
    hwloc_obj_t parent) {
  return hwloc_get_child_covering_cpuset(topology, cpuset, parent);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_covering_cpuset(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset) {
  return hwloc_get_obj_covering_cpuset(topology, cpuset);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_covering_cpuset_by_depth(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset, int depth,
    hwloc_obj_t prev) {
  return hwloc_get_next_obj_covering_cpuset_by_depth(topology, cpuset, depth,
                                                     prev);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_covering_cpuset_by_type(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset,
    hwloc_obj_type_t type, hwloc_obj_t prev) {
  return hwloc_get_next_obj_covering_cpuset_by_type(topology, cpuset, type,
                                                    prev);
}

// Finding objects inside a CPU set
PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_first_largest_obj_inside_cpuset(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset) {
  return hwloc_get_first_largest_obj_inside_cpuset(topology, cpuset);
}

PYHWLOC_EXPORT int
pyhwloc_get_largest_objs_inside_cpuset(hwloc_topology_t topology,
                                       hwloc_const_cpuset_t cpuset,
                                       hwloc_obj_t *objs, int max) {
  return hwloc_get_largest_objs_inside_cpuset(topology, cpuset, objs, max);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_inside_cpuset_by_depth(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset, int depth,
    hwloc_obj_t prev) {
  return hwloc_get_next_obj_inside_cpuset_by_depth(topology, cpuset, depth,
                                                   prev);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_obj_inside_cpuset_by_type(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset,
    hwloc_obj_type_t type, hwloc_obj_t prev) {
  return hwloc_get_next_obj_inside_cpuset_by_type(topology, cpuset, type, prev);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_inside_cpuset_by_depth(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset, int depth,
    unsigned idx) {
  return hwloc_get_obj_inside_cpuset_by_depth(topology, cpuset, depth, idx);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_obj_inside_cpuset_by_type(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset,
    hwloc_obj_type_t type, unsigned idx) {
  return hwloc_get_obj_inside_cpuset_by_type(topology, cpuset, type, idx);
}

PYHWLOC_EXPORT unsigned pyhwloc_get_nbobjs_inside_cpuset_by_depth(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset, int depth) {
  return hwloc_get_nbobjs_inside_cpuset_by_depth(topology, cpuset, depth);
}

PYHWLOC_EXPORT int
pyhwloc_get_nbobjs_inside_cpuset_by_type(hwloc_topology_t topology,
                                         hwloc_const_cpuset_t cpuset,
                                         hwloc_obj_type_t type) {
  return hwloc_get_nbobjs_inside_cpuset_by_type(topology, cpuset, type);
}

PYHWLOC_EXPORT int pyhwloc_get_obj_index_inside_cpuset(
    hwloc_topology_t topology, hwloc_const_cpuset_t cpuset, hwloc_obj_t obj) {
  return hwloc_get_obj_index_inside_cpuset(topology, cpuset, obj);
}

// Looking at Ancestor and Child Objects
PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_ancestor_obj_by_depth(
    hwloc_topology_t topology, int depth, hwloc_obj_t obj) {
  return hwloc_get_ancestor_obj_by_depth(topology, depth, obj);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_ancestor_obj_by_type(
    hwloc_topology_t topology, hwloc_obj_type_t type, hwloc_obj_t obj) {
  return hwloc_get_ancestor_obj_by_type(topology, type, obj);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_common_ancestor_obj(
    hwloc_topology_t topology, hwloc_obj_t obj1, hwloc_obj_t obj2) {
  return hwloc_get_common_ancestor_obj(topology, obj1, obj2);
}

PYHWLOC_EXPORT int pyhwloc_obj_is_in_subtree(hwloc_topology_t topology,
                                             hwloc_obj_t obj,
                                             hwloc_obj_t subtree_root) {
  return hwloc_obj_is_in_subtree(topology, obj, subtree_root);
}

PYHWLOC_EXPORT hwloc_obj_t pyhwloc_get_next_child(hwloc_topology_t topology,
                                                  hwloc_obj_t parent,
                                                  hwloc_obj_t prev) {
  return hwloc_get_next_child(topology, parent, prev);
}

// Helpers for consulting distance matrices
PYHWLOC_EXPORT int
pyhwloc_distances_obj_index(struct hwloc_distances_s *distances,
                            hwloc_obj_t obj) {
  return hwloc_distances_obj_index(distances, obj);
}

PYHWLOC_EXPORT int pyhwloc_distances_obj_pair_values(
    struct hwloc_distances_s *distances, hwloc_obj_t obj1, hwloc_obj_t obj2,
    hwloc_uint64_t *value1to2, hwloc_uint64_t *value2to1) {
  return hwloc_distances_obj_pair_values(distances, obj1, obj2, value1to2,
                                         value2to1);
}

// Distributing items over a topology
PYHWLOC_EXPORT int pyhwloc_distrib(hwloc_topology_t topology,
                                   hwloc_obj_t *roots, unsigned n_roots,
                                   hwloc_cpuset_t *set, unsigned n, int until,
                                   unsigned long flags) {
  return hwloc_distrib(topology, roots, n_roots, set, n, until, flags);
}

// Remove distances between objects
PYHWLOC_EXPORT int pyhwloc_distances_remove_by_type(hwloc_topology_t topology,
                                                    hwloc_obj_type_t type) {
  return hwloc_distances_remove_by_type(topology, type);
}

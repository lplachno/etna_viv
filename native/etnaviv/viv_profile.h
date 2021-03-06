#ifndef H_VIV_PROFILE
#define H_VIV_PROFILE

#include <stdint.h>

struct viv_conn;

/* GPU profile counters */
enum viv_profile_counter
{
    VIV_PROF_GPU_CLOCK                              = 0,  /* never set in kernel */
    VIV_PROF_AXI_CLOCK                              = 1,  /* never set in kernel */
    VIV_PROF_SHADER_CLOCK                           = 2,  /* never set in kernel */
    VIV_PROF_GPU_CLOCK_START                        = 3,  /* never set in kernel */
    VIV_PROF_GPU_CLOCK_END                          = 4,  /* never set in kernel */
    VIV_PROF_GPU_CYCLES_COUNTER                     = 5,  /* reg 00438 */
    VIV_PROF_GPU_TOTAL_READ_64_BYTES_PER_FRAME      = 6,  /* reg 00040 */
    VIV_PROF_GPU_TOTAL_WRITE_64_BYTES_PER_FRAME     = 7,  /* reg 00044 */
    VIV_PROF_PE_PIXEL_COUNT_KILLED_BY_COLOR_PIPE    = 8,  /* PE debug reg 0 */
    VIV_PROF_PE_PIXEL_COUNT_KILLED_BY_DEPTH_PIPE    = 9,  /* PE debug reg 1 */
    VIV_PROF_PE_PIXEL_COUNT_DRAWN_BY_COLOR_PIPE     = 10, /* PE debug reg 2 */
    VIV_PROF_PE_PIXEL_COUNT_DRAWN_BY_DEPTH_PIPE     = 11, /* PE debug reg 3 */
    VIV_PROF_PS_INST_COUNTER                        = 12, /* SH debug reg 7 */
    VIV_PROF_RENDERED_PIXEL_COUNTER                 = 13, /* SH debug reg 8 */
    VIV_PROF_VS_INST_COUNTER                        = 14, /* SH debug reg 9 */
    VIV_PROF_RENDERED_VERTICE_COUNTER               = 15, /* SH debug reg A */
    VIV_PROF_VTX_BRANCH_INST_COUNTER                = 16, /* SH debug reg B */
    VIV_PROF_VTX_TEXLD_INST_COUNTER                 = 17, /* SH debug reg C */
    VIV_PROF_PXL_BRANCH_INST_COUNTER                = 18, /* SH debug reg D */
    VIV_PROF_PXL_TEXLD_INST_COUNTER                 = 19, /* SH debug reg E */
    VIV_PROF_PA_INPUT_VTX_COUNTER                   = 20, /* PA debug reg 3 */
    VIV_PROF_PA_INPUT_PRIM_COUNTER                  = 21, /* PA debug reg 4 */
    VIV_PROF_PA_OUTPUT_PRIM_COUNTER                 = 22, /* PA debug reg 5 */
    VIV_PROF_PA_DEPTH_CLIPPED_COUNTER               = 23, /* PA debug reg 6 */
    VIV_PROF_PA_TRIVIAL_REJECTED_COUNTER            = 24, /* PA debug reg 7 */
    VIV_PROF_PA_CULLED_COUNTER                      = 25, /* PA debug reg 8 */
    VIV_PROF_SE_CULLED_TRIANGLE_COUNT               = 26, /* SE debug reg 0 */
    VIV_PROF_SE_CULLED_LINES_COUNT                  = 27, /* SE debug reg 1 */
    VIV_PROF_RA_VALID_PIXEL_COUNT                   = 28, /* RA debug reg 0 */
    VIV_PROF_RA_TOTAL_QUAD_COUNT                    = 29, /* RA debug reg 1 */
    VIV_PROF_RA_VALID_QUAD_COUNT_AFTER_EARLY_Z      = 30, /* RA debug reg 2 */
    VIV_PROF_RA_TOTAL_PRIMITIVE_COUNT               = 31, /* RA debug reg 3 */
    VIV_PROF_RA_PIPE_CACHE_MISS_COUNTER             = 32, /* RA debug reg 9 */
    VIV_PROF_RA_PREFETCH_CACHE_MISS_COUNTER         = 33, /* RA debug reg A */
    VIV_PROF_RA_EEZ_CULLED_COUNTER                  = 34, /* never set in kernel */
    VIV_PROF_TX_TOTAL_BILINEAR_REQUESTS             = 35, /* TX debug reg 0 */
    VIV_PROF_TX_TOTAL_TRILINEAR_REQUESTS            = 36, /* TX debug reg 1 */
    VIV_PROF_TX_TOTAL_DISCARDED_TEXTURE_REQUESTS    = 37, /* TX debug reg 2 */
    VIV_PROF_TX_TOTAL_TEXTURE_REQUESTS              = 38, /* TX debug reg 3 */
    VIV_PROF_TX_MEM_READ_COUNT                      = 39, /* TX debug reg 5 */
    VIV_PROF_TX_MEM_READ_IN_8B_COUNT                = 40, /* TX debug reg 6 */
    VIV_PROF_TX_CACHE_MISS_COUNT                    = 41, /* TX debug reg 7 */
    VIV_PROF_TX_CACHE_HIT_TEXEL_COUNT               = 42, /* TX debug reg 8 */
    VIV_PROF_TX_CACHE_MISS_TEXEL_COUNT              = 43, /* TX debug reg 9 */
    VIV_PROF_MC_TOTAL_READ_REQ_8B_FROM_PIPELINE     = 44, /* MC debug reg 1 */
    VIV_PROF_MC_TOTAL_READ_REQ_8B_FROM_IP           = 45, /* MC debug reg 2 */
    VIV_PROF_MC_TOTAL_WRITE_REQ_8B_FROM_PIPELINE    = 46, /* MC debug reg 3 */
    VIV_PROF_HI_AXI_CYCLES_READ_REQUEST_STALLED     = 47, /* HI debug reg 0 */
    VIV_PROF_HI_AXI_CYCLES_WRITE_REQUEST_STALLED    = 48, /* HI debug reg 1 */
    VIV_PROF_HI_AXI_CYCLES_WRITE_DATA_STALLED       = 49, /* HI debug reg 2 */
    VIV_PROF_PE_PIXELS_RENDERED_2D                  = 50, /* PE debug reg B */
    VIV_PROF_NUM_COUNTERS
};

struct viv_profile_counter_info
{
    const char *name;
    const char *description;
};

/** Get number of profile counters.
 */
uint32_t viv_get_num_profile_counters(void);

/** Get information about specific profile counter.
 */
struct viv_profile_counter_info *viv_get_profile_counter_info(enum viv_profile_counter id);

/** Read and reset 2D profile counters.
 *  This will return VIV_STATUS_NOT_SUPPORTED if built without profiling support.
 *  Call viv_get_num_profile_counters() to determine how many uint32_ts to reserve for output buffer.
 */
int viv_read_profile_counters_2d(struct viv_conn *conn, uint32_t *out);

/** Read and reset 3D profile counters.
 *  This will return VIV_STATUS_NOT_SUPPORTED if built without profiling support.
 *  Call viv_get_num_profile_counters() to determine how many uint32_ts to reserve for output buffer.
 */
int viv_read_profile_counters_3d(struct viv_conn *conn, uint32_t *out);

#endif


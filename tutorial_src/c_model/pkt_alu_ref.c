/* -----------------------------------------------------------------------------
 * pkt_alu_ref.c - C Golden Reference Model for DPI-C Integration (Ch.12 - Ch.13)
 * Mirrors pkt_alu.sv arithmetic, saturation clamp, and error masking semantics.
 * -------------------------------------------------------------------------- */
#include <stdint.h>

typedef struct {
  uint32_t result;
  uint8_t  err_flag;
} pkt_alu_exp_t;

void pkt_alu_dpi_calc(
    uint32_t op,
    uint32_t a,
    uint32_t b,
    uint32_t sat_en,
    uint32_t sat_limit,
    uint32_t err_mask,
    uint32_t force_err,
    uint32_t *out_result,
    uint32_t *out_err)
{
  uint32_t raw_res = 0;
  uint32_t raw_err = force_err ? 1u : 0u;
  uint32_t a16 = a & 0xFFFFu;
  uint32_t b16 = b & 0xFFFFu;

  switch (op & 0x7u) {
    case 0: raw_res = a16 + b16; break;            /* ADD */
    case 1: raw_res = (a16 - b16); break;          /* SUB (32-bit unsigned wrap matches SV) */
    case 2: raw_res = a16 * b16; break;            /* MUL */
    case 3: raw_res = a16 ^ b16; break;            /* XOR */
    case 4: raw_res = a16; break;                  /* PASS_A */
    default:
      raw_res = 0xDEADBEEFu;
      raw_err = 1u;
      break;
  }

  if (!raw_err && sat_en && (raw_res > (sat_limit & 0xFFFFu))) {
    raw_res = sat_limit & 0xFFFFu;
  }

  *out_result = raw_res;
  *out_err    = (raw_err && !err_mask) ? 1u : 0u;
}

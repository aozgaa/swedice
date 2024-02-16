#include <array>         // for array
#include <cstddef>       // for size_t
#include <cstdint>       // for int64_t
#include <iostream>      // for char_traits, basic_ostream
#include <tuple>         // for tuple
#include <unordered_map> // for unordered_map

#include <boost/container_hash/hash.hpp> // for hash

using namespace std;

constexpr int ROUNDS = 18;
constexpr int MAX_SCORE = (ROUNDS * (ROUNDS + 1)) / 2;
constexpr int DVAL[] = {4, 6, 8, 12, 20};
constexpr size_t NDICE = sizeof(DVAL) / sizeof(DVAL[0]);
constexpr int DMAX[] = {ROUNDS, ROUNDS / 2, ROUNDS / 3, ROUNDS / 4, ROUNDS / 5};

enum Action : char {
  NEW_DIE = 1,
  PROMOTE = 2,
};

// round,score,d4,d6,d8,d12,d20,l4,l6,l8,l12,l20
using DPKey =
    std::tuple<int, int, int, int, int, int, int, int, int, int, int, int>;

unordered_map<DPKey, double, boost::hash<DPKey>> V;

// d4,d6,d8,d12,d20
using Dice = std::tuple<int, int, int, int, int>;
// score,revenue
using PolicyKey = std::tuple<int, Dice>;
// round,score,revenue
std::unordered_map<PolicyKey, int, boost::hash<PolicyKey>> DPPolicy[ROUNDS];

double rollv(int rnd, int score, int r4, int r6, int r8, int r12, int r20,
             int l4, int l6, int l8, int l12, int l20);
double dpv(int rnd, int score, int r4, int r6, int r8, int r12, int r20, int l4,
           int l6, int l8, int l12, int l20);

consteval auto gen_binomp() {
  std::array<std::array<double, ROUNDS + 1>, ROUNDS + 1> nCk{}; // n Choose k
  for (int N = 0; N <= ROUNDS; N++) {
    nCk[N][0] = 1;
  }
  for (int N = 0; N <= ROUNDS; N++) {
    for (int k = 0; k < N; ++k) {
      nCk[N][k + 1] = ((N - k) * nCk[N][k]) / (k + 1);
    }
  }

  std::array<std::array<double, ROUNDS + 1>, NDICE>
      powp{}; // odds of hitting a 1
  std::array<std::array<double, ROUNDS + 1>, NDICE>
      powq{}; // odds of not hitting a 1
  for (int pi = 0; pi < NDICE; ++pi) {
    powp[pi][0] = 1;
    powq[pi][0] = 1;
  }
  for (int pi = 0; pi < NDICE; ++pi) {
    for (int r = 0; r < ROUNDS; r++) {
      powp[pi][r + 1] = powp[pi][r] * 1.0 / DVAL[pi];
      powq[pi][r + 1] = powq[pi][r] * (1 - 1.0 / DVAL[pi]);
    }
  }

  std::array<std::array<std::array<double, NDICE>, ROUNDS + 1>, ROUNDS + 1>
      res{};
  for (int N = 0; N <= ROUNDS; ++N) {
    for (int k = 0; k <= N; ++k) {
      for (int pi = 0; pi < NDICE; ++pi) {
        double p = 1.0 / DVAL[pi];
        double q = 1 - p;
        res[N][k][pi] = nCk[N][k] * powp[pi][N - k] * powq[pi][k];
      }
    }
  }
  return res;
}
// BINOMP[N][k][pi] is the probability of rolling 1 on k of N of the pi'th dice
// (4,6,8,... faces)
constinit auto BINOMP = gen_binomp();

double rollv(int rnd, int score, int r4, int r6, int r8, int r12, int r20,
             int l4, int l6, int l8, int l12, int l20) {
  double res = 0;
  int rnd_ = rnd + 1;
  for (int r4_ = 0; r4_ <= r4; ++r4_) {
    int l4_ = l4 + r4 - r4_;
    double p4 = BINOMP[r4][r4_][0];
    for (int r6_ = 0; r6_ <= r6; ++r6_) {
      int l6_ = l6 + r6 - r6_;
      double p6 = BINOMP[r6][r6_][1];
      for (int r8_ = 0; r8_ <= r8; ++r8_) {
        int l8_ = l8 + r8 - r8_;
        double p8 = BINOMP[r8][r8_][2];
        for (int r12_ = 0; r12_ <= r12; ++r12_) {
          int l12_ = l12 + r12 - r12_;
          double p12 = BINOMP[r12][r12_][3];
          for (int r20_ = 0; r20_ <= r20; ++r20_) {
            int l20_ = l20 + r20 - r20_;
            double p20 = BINOMP[r20][r20_][4];
            double p = p4 * p6 * p8 * p12 * p20;
            int rev_ = r4_ + r6_ + r8_ + r12_ + r20_;
            int score_ = rev_ ? score + rev_ : 0;
            res += p * dpv(rnd_, score_, r4_, r6_, r8_, r12_, r20_, l4_, l6_,
                           l8_, l12_, l20_);
          }
        }
      }
    }
  }
  return res;
}

double dpv(int rnd, int score, int r4, int r6, int r8, int r12, int r20, int l4,
           int l6, int l8, int l12, int l20) {
  if (rnd >= ROUNDS) {
    return score;
  }
  double &v = V[DPKey{rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20}];
  if (v) {
    return v;
  }

  // roll highest numbered legacy dice
  double legacyv = 0.0;
  if (l20) {
    legacyv =
        rollv(rnd, score, r4, r6, r8, r12, r20 + 1, l4, l6, l8, l12, l20 - 1);
  } else if (l12) {
    legacyv =
        rollv(rnd, score, r4, r6, r8, r12 + 1, r20, l4, l6, l8, l12 - 1, l20);
  } else if (l8) {
    legacyv =
        rollv(rnd, score, r4, r6, r8 + 1, r12, r20, l4, l6, l8 - 1, l12, l20);
  } else if (l6) {
    legacyv =
        rollv(rnd, score, r4, r6 + 1, r8, r12, r20, l4, l6 - 1, l8, l12, l20);
  } else if (l4) {
    legacyv =
        rollv(rnd, score, r4 + 1, r6, r8, r12, r20, l4 - 1, l6, l8, l12, l20);
  }
  if (legacyv) {
    return v = legacyv;
  }

  // add a d4
  double addv =
      rollv(rnd, score, r4 + 1, r6, r8, r12, r20, l4, l6, l8, l12, l20);

  // try promo
  double promov = 0;
  if (r4) {
    promov =
        rollv(rnd, score, r4 - 1, r6 + 1, r8, r12, r20, l4, l6, l8, l12, l20);
  } else if (r6) {
    promov =
        rollv(rnd, score, r4, r6 - 1, r8 + 1, r12, r20, l4, l6, l8, l12, l20);
  } else if (r8) {
    promov =
        rollv(rnd, score, r4, r6, r8 - 1, r12 + 1, r20, l4, l6, l8, l12, l20);
  } else if (r12) {
    promov =
        rollv(rnd, score, r4, r6, r8, r12 - 1, r20 + 1, l4, l6, l8, l12, l20);
  }

  if (addv >= promov) {
    DPPolicy[rnd][{score, {r4, r6, r8, r12, r20}}] = Action::NEW_DIE;
    return v = addv;
  } else {
    DPPolicy[rnd][{score, {r4, r6, r8, r12, r20}}] = Action::PROMOTE;
    return v = promov;
  }
}

int main() {
  double v = dpv(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
  cout << v << endl;
  for (int r = 0; r < ROUNDS; ++r) {
    int new_die = 0;
    int promote = 0;
    int entries = DPPolicy[r].size();
    for (const auto &[k, v] : DPPolicy[r]) {
      new_die += (int)(v == Action::NEW_DIE);
      new_die += (int)(v == Action::PROMOTE);
    }
    cout << "round: " << r << ", entries: " << entries
         << ", new_die: " << new_die << ", promote: " << promote
         << ", percent_new: " << ((double)new_die * 100.0) / (new_die + promote)
         << endl;
  }
}

#!/usr/bin/env bash
echo "Bootstrap server for Release Orchestrator IDP"
set -Eeuo pipefail

DEPLOY_USER="${DEPLOY_USER:-deploy}"
APP_DIR="${APP_DIR:-/opt/release-orchestrator-idp}"

log() {
  echo -e "\n[bootstrap] $1"
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must be run from root: sudo bash bootstrap_vm.sh"
    exit 1
  fi
}

install_base_packages() {
  log "Installing basic packages"
  apt-get update
  apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    openssh-server \
    apt-transport-https \
    software-properties-common
}

remove_conflicting_packages() {
  log "Removing conflicting Docker packages if exist"
  apt-get remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc || true
}

setup_docker_repo() {
  log "Connect the official Docker repository"
  install -m 0755 -d /etc/apt/keyrings

  if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
  fi

  local arch codename
  arch="$(dpkg --print-architecture)"
  codename="$(. /etc/os-release && echo "${VERSION_CODENAME}")"

  cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${codename} stable
EOF
}

install_docker() {
  log "Install Docker Engine and Docker Compose plugin"
  apt-get update
  apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

  systemctl enable docker
  systemctl start docker
}

create_deploy_user() {
  if id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
    log "User ${DEPLOY_USER} exists"
  else
    log "Creating a user ${DEPLOY_USER}"
    adduser --disabled-password --gecos "" "${DEPLOY_USER}"
  fi

  usermod -aG docker "${DEPLOY_USER}"
}

prepare_app_dirs() {
  log "Creating application directories"
  mkdir -p "${APP_DIR}/repo"
  mkdir -p "${APP_DIR}/env"

  chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"
  chmod 755 "${APP_DIR}"
}

show_versions() {
  log "Checking the installed versions"
  docker --version
  docker compose version
  systemctl is-active docker
}

final_message() {
  cat <<EOF

Done.

The server is prepared.
User for deployment: ${DEPLOY_USER}
Project directory: ${APP_DIR}

Next:
1. Configure the SSH key for the user ${DEPLOY_USER}
2. Clone the project to ${APP_DIR}/repo
3. Pass the env file to ${APP_DIR}/env/prod.env
4. Run deploy

Important:
- The new docker group can be applied to the user after a new login session.
- Check for ${DEPLOY_USER}:
    su - ${DEPLOY_USER}
    docker ps
EOF
}

main() {
  require_root
  install_base_packages
  remove_conflicting_packages
  setup_docker_repo
  install_docker
  create_deploy_user
  prepare_app_dirs
  show_versions
  final_message
}

main "$@"